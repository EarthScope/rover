
from os import getpid, unlink, listdir
from os.path import join, exists, basename
from queue import Queue
from threading import Thread
from time import time

from .workers import Workers
from .config import DOWNLOAD, MULTIPROCESS
from .index import Indexer
from .ingest import MseedindexIngester
from .sqlite import SqliteSupport, NoResult
from .utils import canonify, lastmod, uniqueish, get_to_file


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

    def __init__(self, dbpath, tmpdir, mseedindex, mseed_dir, leap, leap_expire, leap_file, leap_url, n_workers, log):
        super().__init__(dbpath, log)
        self._tmpdir = canonify(tmpdir)
        self._blocksize = 1024 * 1024
        self._ingester = MseedindexIngester(mseedindex, dbpath, mseed_dir, leap, leap_expire, leap_file, leap_url, log)
        self._indexer = Indexer(mseedindex, dbpath, mseed_dir, n_workers, leap, leap_expire, leap_file, leap_url, log)
        self._create_downloaderss_table()
        self._clean_tmp()

    def _clean_tmp(self):
        if exists(self._tmpdir):
            for file in listdir(self._tmpdir):
                if basename(file).startswith(TMPFILE):
                    if time() - lastmod(file) > TMPEXPIRE:
                        self._log.warn('Deleting old download %s' % file)

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


def download(args, log):
    """
    Implement the download command - download, ingest and index data.
    """
    downloader = Downloader(args.mseed_db, args.temp_dir, args.mseed_cmd, args.mseed_dir,
                           args.leap, args.leap_expire, args.leap_file, args.leap_url, args.mseed_workers, log)
    if len(args.args) != 1:
        raise Exception('Usage: rover %s url' % DOWNLOAD)
    downloader.download(args.args[0])


class DownloadManager:

    def __init__(self, n_workers, dataselect, log):
        self._log = log
        self._dataselect = dataselect
        self._queue = Queue()
        self._workers = Workers(n_workers, log)
        Thread(target=self._main_loop).start()

    def download(self, coverage):
        # todo expand coverage to days
        for download in self._expand_timespans(coverage):
            self._queue.push(download)

    def _expand_timespans(self, coverage):
        yield None

    def wait_for_all(self):
        self._queue.join()
        # no need to kill thread as it is non-daemon - ok to leave it blocked on empty queue

    def _build_url(self, sncl, begin, end):
        return '%s?%s&start=%s&end=%s' % (self._dataselect, sncl.to_url_params(), begin, end)

    def _callback(self, command, returncode):
        if returncode:
            self._log.error('Download %s returned %d' % (command, returncode))
        self._queue.task_done()

    def _main_loop(self):
        while True:
            sncl, begin, end = self._queue.get()
            command = 'rover --%s %s %s' % (MULTIPROCESS, DOWNLOAD, self._build_url(sncl, begin, end))
            self._workers.execute(command, callback=self._callback)
