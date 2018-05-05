
from datetime import datetime, timedelta
from os import getpid, unlink, listdir
from os.path import join, exists, basename
from queue import Queue, Empty
from threading import Thread
from time import time

from .workers import Workers
from .config import DOWNLOAD, MULTIPROCESS, MSEEDCMD, VERBOSITY, LOGNAME, LOGUNIQUE, mm, DEV, Arguments
from .index import Indexer
from .ingest import MseedindexIngester
from .sqlite import SqliteSupport, NoResult
from .utils import canonify, lastmod, uniqueish, get_to_file, PushBackIterator, format_time, check_cmd, unique_filename

# if a download process fails or hangs, we need to clear out
# the file, so use a specific name and check for old files
# in the download area
TMPFILE = 'rover_tmp'
TMPEXPIRE = 60 * 60 * 24


class Downloader(SqliteSupport):
    """
    Download a single request (typically for a day), ingest and index it.

    The only complex thing here is that these may run in parallel and call ingest.
    That means that multiple ingest instances can be running in parallel, all using
    temp tables in the database.  So we need to manage temp table names and clear
    out old tables from crashed processes.

    To do this we have another table that is a list of retrievers, along with
    URLs, PIDs, table names and epochs.

    This isn't a problem for the main ingest command because only
    a sin=gle instance of the command line command runs at any one
    time.
    """

    def __init__(self, db, tmpdir, mseedindex, mseed_db, mseed_dir, leap, leap_expire, leap_file, leap_url, n_workers, dev, log):
        super().__init__(db, log)
        self._tmpdir = canonify(tmpdir)
        self._blocksize = 1024 * 1024
        self._ingester = MseedindexIngester(db, mseedindex, mseed_db, mseed_dir, leap, leap_expire, leap_file, leap_url, log)
        self._indexer = Indexer(db, mseedindex, mseed_db, mseed_dir, n_workers, leap, leap_expire, leap_file, leap_url, dev, log)
        self._create_downloaderss_table()
        self._clean_tmp()

    def _clean_tmp(self):
        if exists(self._tmpdir):
            for file in listdir(self._tmpdir):
                if basename(file).startswith(TMPFILE):
                    try:
                        if time() - lastmod(file) > TMPEXPIRE:
                            self._log.warn('Deleting old download %s' % file)
                    except FileNotFoundError:
                        pass  # was deleted from under us


    def download(self, url):
        """
        Download the give URL, then call ingest and index before deleting.
        """
        self._assert_single_use()
        retrievers_id, table = self._update_retrievers_table(url)
        path = None
        try:
            path = self._do_download(url)
            self._ingester.ingest([path], table=table)
            self._indexer.index()
        finally:
            if path: unlink(path)
            self._execute('drop table if exists %s' % table)
            self._execute('delete from rover_downloaders where id = ?', (retrievers_id,))

    def _update_retrievers_table(self, url):
        self._clear_dead_retrievers()
        pid = getpid()
        table = self._retrievers_table_name(url, pid)
        self._execute('insert into rover_downloaders (pid, table_name, url) values (?, ?, ?)', (pid, table, url))
        id = self._fetchsingle('select id from rover_downloaders where pid = ? and table_name like ? and url like ?',
                               (pid, table, url))  # todo - auto retrieve key?
        return id, table

    def _do_download(self, url):
        # previously we extracted the file name from the header, but the code
        # failed in python 2 (looked like a backport library bug), so since
        # the file will be deleted soon anyway we now use an arbitrary name
        path = join(self._tmpdir, uniqueish(TMPFILE, url))
        return get_to_file(url, path, self._log)


def download(core):
    """
    Implement the download command - download, ingest and index data.
    """
    downloader = Downloader(core.db, core.args.temp_dir, core.args.mseed_cmd, core.args.mseed_db, core.args.mseed_dir,
                            core.args.leap, core.args.leap_expire, core.args.leap_file, core.args.leap_url,
                            core.args.mseed_workers, core.args.dev, core.log)
    if len(core.args.args) != 1:
        raise Exception('Usage: rover %s url' % DOWNLOAD)
    downloader.download(core.args.args[0])


class DownloadManager:
    """
    An interface to downloader instances that restricts downloads to a fixed number of workers,
    each downloading data that is for a maximum duration of a day.

    Used in two steps.  First, coverage data are added (via 'add).  Then these are expanded to
    timespans that are processed as workers (in the 'run' method).

    This acts as a buffer, soaking up all the requests from the Retriever so that can
    run through the database as quicky as possible, but avoiding expanding that into too
    many timespans (which could consume a lot of memory if the user requests a large
    date range).

    (I'm not sure this is actually worthwhile - is memory use really such a problem?  If
    not then we could avoid the multi-threading here, simply expanding into memory and
    then pushing those to workers).
    """

    def __init__(self, n_workers, dataselect, rover, mseedindex, tmpdir, verbosity, dev, log_unique, args, log):
        self._log = log
        self._dataselect = dataselect
        check_cmd('%s -h' % rover, 'rover', 'rover', log)
        self._rover = rover
        check_cmd('%s -h' % mseedindex, 'mseedindex', 'mseed-cmd', log)
        self._mseedindex = mseedindex
        self._tmpdir = tmpdir
        self._verbosity = verbosity
        self._dev = dev
        self._log_unique = log_unique
        self._args = args
        self._coverages = []
        self._queue = Queue(maxsize=n_workers * 2)
        self._workers = Workers(n_workers, log)
        self._run_called = False
        self._config = None

    def add(self, coverage):
        if self._run_called:
            raise Exception('Add coverage before expanding and downloading')
        self._coverages.append(coverage)

    def run(self):
        self._run_called = True
        self._config = self._write_config()
        Thread(target=self._main_loop, daemon=True).start()
        try:
            for coverage in self._coverages:
                for download in self._expand_timespans(coverage):
                    self._queue.put(download)  # this blocks so that we don't use too much memory
            self._queue.join()
            # no need to kill thread as it is a daemon - ok to leave it blocked on empty queue
        finally:
            unlink(self._config)

    def _write_config(self):
        if self._coverages:
            junk = str(self._coverages[0])
        else:
            junk = 'empty'
        path = unique_filename(join(canonify(self._tmpdir), uniqueish('rover_config', junk)))
        self._log.debug('Writing config to %s' % path)
        Arguments().write_config(path, self._args)
        return path

    def _end_of_day(self, day):
        right = datetime(day.year, day.month, day.day) + timedelta(hours=24)
        left = right - timedelta(milliseconds=0.000001)
        return left, right

    def _expand_timespans(self, coverage):
        sncl, timespans = coverage.sncl, PushBackIterator(iter(coverage.timespans))
        while True:
            begin, end = next(timespans)
            if begin.date == end.date:
                yield sncl, begin, end
            else:
                left, right = self._end_of_day(begin)
                yield sncl, begin, min(left, end)
                if right < end:
                    timespans.push((right, end))

    def _build_url(self, sncl, begin, end):
        return '%s?%s&start=%s&end=%s' % (self._dataselect, sncl.to_url_params(), format_time(begin), format_time(end))

    def _callback(self, command, returncode):
        if returncode:
            self._log.error('Download %s returned %d' % (command, returncode))
        self._queue.task_done()

    def _main_loop(self):
        while True:
            try:
                sncl, begin, end = self._queue.get(timeout=0.1)
                command = '%s -f \'%s\' %s %s %s %s %s %s \'%s\'' % (
                    self._rover, self._config, mm(MULTIPROCESS), mm(LOGNAME), DOWNLOAD,
                    mm(LOGUNIQUE) if self._log_unique else '',  mm(DEV) if self._dev else '',
                    DOWNLOAD, self._build_url(sncl, begin, end))
                self._log.debug(command)
                self._workers.execute(command, callback=self._callback)
            except Empty:
                # important to clear these out so that they hit teh callback and empty
                # the count for the queue, allowing the entire program to exit.
                self._workers.check()
