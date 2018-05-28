
import datetime
from collections import deque
from os import getpid
from os.path import join, exists
from time import sleep

from .args import DOWNLOAD, MULTIPROCESS, LOGNAME, LOGUNIQUE, mm, DEV, Arguments, TEMPDIR, DELETEFILES, INGEST, \
    TEMPEXPIRE, DATASELECTURL, ROVERCMD, MSEEDCMD, DOWNLOADWORKERS
from .ingest import Ingester
from .sqlite import SqliteSupport
from .utils import canonify, uniqueish, get_to_file, check_cmd, unique_filename, \
    clean_old_files, match_prefixes, PushBackIterator, utc, EPOCH_UTC, format_epoch, create_parents, unique_path, \
    canonify_dir_and_make, safe_unlink
from .workers import Workers

"""
The 'rover download' command - download data from a URL (and then call ingest).

(and the DownloadManager buffer that 'rover retrieve' calls, which spawns multiple Downloaders). 
"""


# if a download process fails or hangs, we need to clear out
# the file, so use a specific name and check for old files
# in the download area
TMPFILE = 'rover_download'
CONFIGFILE = 'rover_config'


class Downloader(SqliteSupport):
    """
### Download

    rover download url [path]

Download a single request (typically for a day) to teh given path, ingest and index it.  If no path is given then
a temporary file is created and deleted after use.

The url should be for a Data Select service, and should not request data that spans multiple calendar days.

##### Significant Parameters

@temp-dir
@delete-files
@ingest
@index
@verbosity
@log-dir
@log-name
@log-verbosity

In addition, parameters for sub-commands (ingest, index) will be used - see help for those
commands for more details.

##### Examples

    rover download \\
    http://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2010-02-27T06:30:00.000&end=2010-02-27T10:30:00.000

will download, ingest and index data from the given URL..

"""

# The only complex thing here is that these may run in parallel.  That means that
# multiple ingest instances can be running in parallel, all using mseedindex.
# To avoid conflict over sqlite access we use a different database file for each,
# so we need to track and delete those.
#
# To do this we have a table that lists ingesters, along with URLs, PIDs,
# database paths and epochs.
#
# This isn't a problem for the main ingest command because only a single instance
# of the command line command runs at any one time.

    def __init__(self, config):
        SqliteSupport.__init__(self, config)
        self._temp_dir = config.dir_path(TEMPDIR)
        self._delete_files = config.arg(DELETEFILES)
        self._blocksize = 1024 * 1024
        self._ingest = config.arg(INGEST)
        self._config = config
        clean_old_files(self._temp_dir, config.arg(TEMPEXPIRE), match_prefixes(TMPFILE), self._log)

    def run(self, args):
        """
        Download the give URL, then call ingest and index before deleting.
        """
        if len(args) < 1 or len(args) > 2:
            raise Exception('Usage: rover %s url [path]' % DOWNLOAD)
        url = args[0]
        if len(args) == 2:
            path, delete = args[2], False
        else:
            path, delete = unique_path(self._temp_dir, TMPFILE, url), True
        db_path = self._ingesters_db_path(url, getpid())
        try:
            self._do_download(url, path)
            if self._ingest:
                Ingester(self._config).run([path], db_path=db_path)
        finally:
            if self._delete_files:
                if path and delete:
                    safe_unlink(path)
                safe_unlink(db_path)

    def _do_download(self, url, path):
        # previously we extracted the file name from the header, but the code
        # failed in python 2 (looked like a backport library bug), so now we let the user specify,
        if exists(path):
            raise Exception('Path %s for download already exists' % path)
        create_parents(path)
        return get_to_file(url, path, self._log)

    def _ingesters_db_path(self, url, pid):
        name = uniqueish('rover_ingester', url)
        return unique_filename(join(self._temp_dir, name))


class Source:
    """
    Data for a single source in the download manager.
    """

    def __init__(self, name, dataselect_url):
        self._name = name
        self._dataselect_url = dataselect_url
        self._coverages = deque()  # fifo: appendright / popleft; exposed for display
        self._days = deque()  # fifo: appendright / popleft
        self.worker_count = 0
        self.new = True  # avoid deletion when first created and empty

    def __str__(self):
        return '%s (%s)' % (self._name, self._dataselect_url)

    def add_coverage(self, coverage):
        self.new = False
        self._coverages.append(coverage)

    def get_coverages(self):
        return list(self._coverages)

    @staticmethod
    def _end_of_day(epoch):
        day = datetime.datetime.fromtimestamp(epoch, utc)
        right = (datetime.datetime(day.year, day.month, day.day, tzinfo=utc)
                 + datetime.timedelta(hours=24) - EPOCH_UTC).total_seconds()
        left = right - 0.000001
        return left, right

    def has_days(self):
        """
        Ensure days has some data, if possible, and return whether it has any.
        """
        if self._days:
            return True
        while self._coverages:
            coverage = self._coverages.popleft()
            sncl, timespans = coverage.sncl, PushBackIterator(iter(coverage.timespans))
            for begin, end in timespans:
                if begin == end:
                    self._days.append((sncl, begin, end))
                else:
                    left, right = self._end_of_day(begin)
                    self._days.append((sncl, begin, min(left, end)))
                    if right < end:
                        timespans.push((right, end))
            if self._days:
                return True
        return False

    def _build_url(self, sncl, begin, end):
        url_params = 'net=%s&sta=%s&loc=%s&cha=%s' % tuple(sncl.split('.'))
        return '%s?%s&start=%s&end=%s' % (self._dataselect_url, url_params, format_epoch(begin), format_epoch(end))

    def _callback(self, command, return_code):
        self.worker_count -= 1

    def new_worker(self, log, workers, config_path, rover_cmd, log_unique, dev):
        url = self._build_url(*self._days.popleft())
        # we only pass arguments on the command line that are different from the
        # default (which is in the file)
        command = '%s -f \'%s\' %s %s %s %s %s %s \'%s\'' % (
            rover_cmd, config_path, mm(MULTIPROCESS), mm(LOGNAME), DOWNLOAD,
            mm(LOGUNIQUE) if log_unique else '', mm(DEV) if dev else '', DOWNLOAD, url)
        log.debug(command)
        workers.execute(command, self._callback)
        self.worker_count += 1

    def is_complete(self):
        return not self.new and self.worker_count == 0 and not self.has_days()


class DownloadManager:
    """
    An interface to downloader instances that restricts downloads to a fixed number of workers,
    each downloading data that is for a maximum duration of a day.

    It supports multiple *sources* and will try to divide load fairly between sources.  A
    source is typically a source / subscription, so we spread downloads across multiple
    servers when possible.

    The config_file is overwritten (in temp_dir) because only a singleton (for either
    standalone or daemon) should ever exist.  Because of this, and the daemon exiting via
    kill(), no attempt is made to delete the file on exit.

    IMPORTANT: This is used from a SINGLE thread.  So for it to work reliably the step()
    method must be called regularly (perhaps via download()).
    """

    def __init__(self, config, config_file):
        super().__init__()
        self._log = config.log
        self._rover_cmd = check_cmd(config.arg(ROVERCMD), 'rover', 'rover-cmd', config.log)
        self._mseed_cmd = check_cmd(config.arg(MSEEDCMD), 'mseedindex', 'mseed-cmd', config.log)
        self._dev = config.arg(DEV)
        self._log_unique = config.arg(LOGUNIQUE)
        self._sources = {}  # map of source names to sources
        self._index = 0  # used to round-robin sources
        self._workers = Workers(config, config.arg(DOWNLOADWORKERS))
        self._n_downloads = 0
        temp_dir = config.arg(TEMPDIR)
        self._config_path = self._write_config(temp_dir, config_file, config.absolute()._args)
        clean_old_files(temp_dir, config.arg(TEMPEXPIRE), match_prefixes(CONFIGFILE), self._log)

    def _write_config(self, temp_dir, config_file, args):
        temp_dir = canonify_dir_and_make(temp_dir)
        config_path = join(temp_dir, config_file)
        safe_unlink(config_path)
        Arguments().write_config(config_path, args)
        return config_path

    def add_source(self, source, dataselect_url):
        if source in self._sources and self._sources[source].worker_count:
            raise Exception('Cannot overwrite active source %s' % self._sources[source])
        self._sources[source] = Source(source, dataselect_url)

    def has_source(self, name):
        return name in self._sources

    def _source(self, name):
        if name not in self._sources:
            raise Exception('Unexpected source: %s' % name)
        return self._sources[name]

    def add_coverage(self, source, coverage):
        """
        Add a required Coverage (SNCL and associated timespans).  This will be expanded
        into one or more downloads by the source's Expander.
        """
        self._source(source).add_coverage(coverage)

    def display(self):
        """
        Display a summary of the data that have not been expanded into downloads.
        """
        total_seconds, total_sncls = 0, 0
        for name in self._sources.keys():
            source = self._sources[name]
            coverages = source.get_coverages()
            print()
            if len(self._sources) > 1:
                print('Source %s (%s)' % source)
                print()
            source_seconds, source_sncls = 0, 0
            for coverage in coverages:
                sncl_seconds = 0
                for (begin, end) in coverage.timespans:
                    seconds = end - begin
                    sncl_seconds += seconds
                    source_seconds += seconds
                    total_seconds += seconds
                if sncl_seconds:
                    source_sncls += 1
                    total_sncls += 1
                    print('  %s  (%4.2f sec)' % (coverage.sncl, sncl_seconds))
                    for (begin, end) in coverage.timespans:
                        print('    %s - %s  (%4.2f sec)' % (format_epoch(begin), format_epoch(end), end - begin))
            if len(self._sources) > 1:
                print()
                print('  %s: %d SNCLSs; %4.2f sec' % (name, source_sncls, source_seconds))
        if total_sncls:
            print()
        print('  Total: %d SNCLSs; %4.2f sec' % (total_sncls, total_seconds))
        print()
        return total_sncls

    def _has_data(self):
        for source in self._sources.values():
            if source.has_days():
                return True
        return False

    def _next_source(self, sources):
        self._index = (self._index + 1) % len(sources)
        return sources[self._index]

    def _has_least_workers(self, c):
        for source in self._sources.values():
            if not source.new and source.worker_count < c.worker_count:
                return False
        return True

    def _clean_sources(self):
        names = list(self._sources.keys())
        for name in names:
            if self._source(name).is_complete():
                self._log.debug('Source %s complete' % self._source(name))
                del self._sources[name]

    def is_idle(self):
        self._clean_sources()
        return len(self._sources) == 0

    def step(self):
        """
        A single iteration of the manager's main loop.  Can be inter-mixed with add_source and add_coverage.
        Cleaning logic assumes coverages for a source are all added at once, though.  If you don't, source
        may be deleted when you don't expect it.
        """
        self._workers.check()
        self._clean_sources()
        while self._workers.has_space() and self._has_data():
            sources = list(
                filter(lambda source: not source.new,
                    map(lambda name: self._source(name),
                        sorted(self._sources.keys()))))
            while True:
                source = self._next_source(sources)
                if self._has_least_workers(source): break
            if source.has_days():
                source.new_worker(self._log, self._workers, self._config_path, self._rover_cmd, self._log_unique, self._dev)
                self._n_downloads += 1

    def download(self):
        """
        Run to completion.  For single-shot, called after add_source and add_coverage.
        """
        try:
            while self._sources:
                self.step()
                sleep(0.1)
        finally:
            # not needed in normal use, as no workers when no sources, but useful on error
            self._workers.wait_for_all()
            if self._n_downloads:
                self._log.info('Completed %d downloads' % self._n_downloads)
            else:
                self._log.warn('No data downloaded / ingested')
        return self._n_downloads
