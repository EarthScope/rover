
import datetime
from os import getpid, unlink
from os.path import join
from queue import Queue, Empty
from threading import Thread
from time import time

from .args import DOWNLOAD, MULTIPROCESS, LOGNAME, LOGUNIQUE, mm, DEV, Arguments
from .coverage2 import format_epoch, EPOCH_UTC
from .ingest import Ingester
from .sqlite import SqliteSupport
from .utils import canonify, uniqueish, get_to_file, check_cmd, unique_filename, \
    clean_old_files, match_prefixes, PushBackIterator, utc
from .workers import Workers

# if a download process fails or hangs, we need to clear out
# the file, so use a specific name and check for old files
# in the download area
TMPFILE = 'rover_tmp'
CONFIGFILE = 'rover_config'


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

    def __init__(self, config):
        super().__init__(config)
        args = config.args
        self._temp_dir = canonify(args.temp_dir)
        self._delete_files = args.delete_files
        self._delete_tables = args.delete_tables
        self._blocksize = 1024 * 1024
        self._ingester = Ingester(config)
        self._create_downloaderss_table()
        clean_old_files(self._temp_dir, args.temp_expire, match_prefixes(TMPFILE, CONFIGFILE), self._log)

    def run(self, url):
        """
        Download the give URL, then call ingest and index before deleting.
        """
        self._assert_single_use()
        retrievers_id, table = self._update_retrievers_table(url)
        path = None
        try:
            path = self._do_download(url)
            self._ingester.run([path], table=table)
        finally:
            if path and self._delete_files: unlink(path)
            if self._delete_tables:
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

    def _clear_dead_retrievers(self):
        if self._delete_tables:
            for row in self._fetchall('select id, table_name from rover_downloaders where creation_epoch < ?', (time() - 60 * 60,)):
                id, table = row
                self._log.warn('Forcing deletion of table %s' % table)
                self._execute('drop table if exists %s' % table)
                self._execute('delete from rover_downloaders where id = ?', (id,))

    def _do_download(self, url):
        # previously we extracted the file name from the header, but the code
        # failed in python 2 (looked like a backport library bug), so since
        # the file will be deleted soon anyway we now use an arbitrary name
        path = join(self._temp_dir, uniqueish(TMPFILE, url))
        return get_to_file(url, path, self._log)


def download(config):
    """
    Implement the download command - download, ingest and index data.
    """
    downloader = Downloader(config)
    args = config.args.args
    if len(args) != 1:
        raise Exception('Usage: rover %s url' % DOWNLOAD)
    downloader.run(args[0])


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

    def __init__(self, config):
        args, log = config.args, config.log
        self._log = log
        self._dataselect_url = args.dataselect_url
        check_cmd('%s -h' % args.rover_cmd, 'rover', 'rover', log)
        self._rover_cmd = args.rover_cmd
        check_cmd('%s -h' % args.mseed_cmd, 'mseedindex', 'mseed-cmd', log)
        self._mseed_cmd = args.mseed_cmd
        self._temp_dir = canonify(args.temp_dir)
        self._dev = args.dev
        self._log_unique = args.log_unique
        self._args = args
        self._coverages = []
        self._queue = Queue(maxsize=args.download_workers * 2)
        self._workers = Workers(config, args.download_workers)
        self._download_called = False
        self._config_path = None

    def add(self, coverage):
        if self._download_called:
            raise Exception('Add coverage before expanding and downloading')
        self._coverages.append(coverage)

    def display(self):
        """
        Display a asummary of the data.
        """
        print()
        total_seconds, total_sncls = 0, 0
        for coverage in self._coverages:
            sncl_seconds = 0
            for (begin, end) in coverage.timespans:
                seconds = end - begin
                sncl_seconds += seconds
                total_seconds += seconds
            if sncl_seconds:
                total_sncls += 1
                print('  %s  (%4.2f sec)' % (coverage.sncl, sncl_seconds))
                for (begin, end) in coverage.timespans:
                    print('    %s - %s  (%4.2f sec)' % (format_epoch(begin), format_epoch(end), end - begin))
        if total_sncls:
            print()
        print('  Total: %d SNCLSs; %4.2f sec' % (total_sncls, total_seconds))
        print()
        return total_sncls

    def download(self):
        """
        Expand the timespans into daily downloads, get the data and ingest.
        """
        self._download_called = True
        self._config_path = self._write_config()
        daemon = Thread(target=self._main_loop)
        daemon.daemon = True  # py2.7 not available in constructor
        daemon.start()
        n_downloads = 0
        try:
            for coverage in self._coverages:
                for download in self._expand_timespans(coverage):
                    self._queue.put(download)  # this blocks so that we don't use too much memory
                    n_downloads += 1
            self._queue.join()
            # no need to kill thread as it is a daemon - ok to leave it blocked on empty queue
            if n_downloads:
                self._log.info('Completed %d downloads' % n_downloads)
            else:
                self._log.warn('No data downloaded / ingested')
        finally:
            unlink(self._config_path)
        return n_downloads

    def _write_config(self):
        if self._coverages:
            junk = str(self._coverages[0])
        else:
            junk = 'empty'
        path = unique_filename(join(canonify(self._temp_dir), uniqueish(CONFIGFILE, junk)))
        self._log.debug('Writing config to %s' % path)
        Arguments().write_config(path, self._args)
        return path

    def _end_of_day(self, epoch):
        day = datetime.datetime.fromtimestamp(epoch, utc)
        right = (datetime.datetime(day.year, day.month, day.day, tzinfo=utc)
                 + datetime.timedelta(hours=24) - EPOCH_UTC).total_seconds()
        left = right - 0.000001
        return left, right

    def _expand_timespans(self, coverage):
        sncl, timespans = coverage.sncl, PushBackIterator(iter(coverage.timespans))
        while True:
            begin, end = next(timespans)
            if begin == end:
                yield sncl, begin, end
            else:
                left, right = self._end_of_day(begin)
                yield sncl, begin, min(left, end)
                if right < end:
                    timespans.push((right, end))

    def _build_url(self, sncl, begin, end):
        url_params = 'net=%s&sta=%s&loc=%s&cha=%s' % tuple(sncl.split('.'))
        return '%s?%s&start=%s&end=%s' % (self._dataselect_url, url_params, format_epoch(begin), format_epoch(end))

    def _callback(self, command, returncode):
        if returncode:
            self._log.error('Download %s returned %d' % (command, returncode))
        self._queue.task_done()

    def _main_loop(self):
        while True:
            try:
                sncl, begin, end = self._queue.get(timeout=0.1)
                # we only pass arguments on the command line that are different from the
                # default (which is in the file)
                command = '%s -f \'%s\' %s %s %s %s %s %s \'%s\'' % (
                    self._rover_cmd, self._config_path, mm(MULTIPROCESS), mm(LOGNAME), DOWNLOAD,
                    mm(LOGUNIQUE) if self._log_unique else '', mm(DEV) if self._dev else '',
                    DOWNLOAD, self._build_url(sncl, begin, end))
                self._log.debug(command)
                self._workers.execute(command, callback=self._callback)
            except Empty:
                # important to clear these out so that they hit teh callback and empty
                # the count for the queue, allowing the entire program to exit.
                self._workers.check()
