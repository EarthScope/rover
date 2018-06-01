
import datetime
from collections import deque
from os import getpid
from os.path import join, exists
from sqlite3 import OperationalError
from subprocess import Popen
from time import sleep, time

from .args import DOWNLOAD, LOGUNIQUE, mm, DEV, TEMPDIR, DELETEFILES, INGEST, \
    TEMPEXPIRE, ROVERCMD, MSEEDINDEXCMD, DOWNLOADWORKERS, TIMESPANTOL, LOGVERBOSITY, VERBOSITY, WEB
from .config import write_config
from .coverage import Coverage, SingleSNCLBuilder
from .ingest import Ingester
from .sqlite import SqliteSupport
from .utils import uniqueish, get_to_file, check_cmd, unique_filename, \
    clean_old_files, match_prefixes, PushBackIterator, utc, EPOCH_UTC, format_epoch, create_parents, unique_path, \
    safe_unlink, post_to_file, parse_epoch, sort_file_inplace, file_size
from .workers import Workers

"""
The 'rover download' command - download data from a URL (and then call ingest).

(and the DownloadManager buffer that 'rover retrieve' and 'rover daemon' call, which spawns multiple Downloaders). 
"""


TMPREQUEST = 'rover_availability_request'
TMPRESPONSE = 'rover_availability_response'
TMPDOWNLOAD = 'rover_download'

# name of source when not a subscription
DEFAULT_NAME = -1


class Downloader(SqliteSupport):
    """
### Download

    rover download url [path]

Download a single request (typically for a day) to the given path, ingest and index it.  If no path is given then
a temporary file is created and deleted after use.

The url should be for a Data Select service, and should not request data that spans multiple calendar days.

This task is the main low-level task called in the processing pipeline (it calls ingest and index as needed).
Because of this, to reduce the quantity of unhelpful logs generated when a pipeline is running, empty logs are
automatically deleted on exit.

##### Significant Parameters

@temp-dir
@delete-files
@ingest
@index
@verbosity
@log-dir
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
        clean_old_files(self._temp_dir, config.arg(TEMPEXPIRE), match_prefixes(TMPDOWNLOAD), self._log)

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
            path, delete = unique_path(self._temp_dir, TMPDOWNLOAD, url), True
        db_path = self._ingesters_db_path(url, getpid())
        try:
            self._do_download(url, path)
            if self._ingest:
                Ingester(self._config).run([path], db_path=db_path)
        finally:
            if self._delete_files:
                if path and delete:
                    safe_unlink(path)
                log_path = self._config.log_path
                # avoid lots of empty logs cluttering things up
                if exists(log_path) and file_size(log_path) == 0:
                    safe_unlink(log_path)
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


NOSTATS = (-1, -1)


class Source:
    """
    Data for a single source in the download manager.
    """

    def __init__(self, name, dataselect_url, completion_callback):
        self.name = name
        self._dataselect_url = dataselect_url
        self._completion_callback = completion_callback
        self._coverages = deque()  # fifo: appendright / popleft; exposed for display
        self._days = deque()  # fifo: appendright / popleft
        self.initial_stats = NOSTATS
        self.worker_count = 0
        self.n_downloads = 0
        self.n_errors = 0
        self.start_epoch = time()

    def __str__(self):
        return '%s (%s)' % (self.name, self._dataselect_url)

    def add_coverage(self, coverage):
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

    def stats(self):
        coverage_count, total_seconds = 0, 0
        for coverage in self._coverages:
            coverage_count += 1
            for timespan in coverage.timespans:
                begin, end = timespan
                total_seconds += (end - begin)
        return coverage_count, total_seconds

    def has_days(self):
        """
        Ensure days has some data, if possible, and return whether it has any.
        """
        if self.initial_stats == NOSTATS:
            self.initial_stats = self.stats()
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
        url_params = 'net=%s&sta=%s&loc=%s&cha=%s' % tuple(sncl.split('_'))
        return '%s?%s&start=%s&end=%s' % (self._dataselect_url, url_params, format_epoch(begin), format_epoch(end))

    def _worker_callback(self, command, return_code):
        self.worker_count -= 1
        self.n_downloads += 1
        if return_code:
            self.n_errors += 1

    def new_worker(self, log, workers, config_path, rover_cmd):
        url = self._build_url(*self._days.popleft())
        # we only pass arguments on the command line that are different from the
        # default (which is in the file)
        command = '%s -f \'%s\' %s \'%s\'' % (rover_cmd, config_path, DOWNLOAD, url)
        log.debug(command)
        workers.execute(command, self._worker_callback)
        self.worker_count += 1

    def is_complete(self):
        complete = self.worker_count == 0 and not self.has_days()
        if complete and self._completion_callback:
            self._completion_callback(self)
            self._completion_callback = None
        return complete


class DownloadManager(SqliteSupport):
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

    def __init__(self, config, config_file=None):
        super().__init__(config)
        self._log = config.log
        self._timespan_tol = config.arg(TIMESPANTOL)
        self._temp_dir = config.dir_path(TEMPDIR)
        self._delete_files = config.arg(DELETEFILES)
        self._sources = {}  # map of source names to sources
        self._index = 0  # used to round-robin sources
        self._workers = Workers(config, config.arg(DOWNLOADWORKERS))
        self._n_downloads = 0
        self._create_stats_table()
        if config_file:
            # these aren't used to list subscriptions (when config_file is None)
            self._rover_cmd = check_cmd(config, ROVERCMD, 'rover')
            self._mseed_cmd = check_cmd(config, MSEEDINDEXCMD, 'mseedindex')
            log_unique = config.arg(LOGUNIQUE) or not config.arg(DEV)
            log_verbosity = config.arg(LOGVERBOSITY) if config.arg(DEV) else min(config.arg(LOGVERBOSITY), 3)
            self._config_path = write_config(config, config_file, log_unique=log_unique, log_verbosity=log_verbosity)
            self._start_web()
        else:
            self._config_path = None

    # source management

    def has_source(self, name):
        """
        Is the given source known (they are deleted once all data are downloaded).
        """
        return name in self._sources

    def _source(self, name):
        if name not in self._sources:
            raise Exception('Unexpected source: %s' % name)
        return self._sources[name]

    # querying availability service and adding coverage

    def _build_request(self, path):
        tmp = unique_path(self._temp_dir, TMPREQUEST, path)
        self._log.debug('Prepending options to %s via %s' % (path, tmp))
        with open(tmp, 'w') as output:
            print('mergequality=true', file=output)
            print('mergesamplerate=true', file=output)
            with open(path, 'r') as input:
                for line in input:
                    print(line, file=output, end='')
        return tmp

    def _get_availability(self, request, availability_url):
        response = unique_path(self._temp_dir, TMPRESPONSE, request)
        response = post_to_file(availability_url, request, response, self._log)
        sort_file_inplace(self._log, response, self._temp_dir)
        return response

    def _parse_line(self, line):
        n, s, l, c, b, e = line.split()
        return "%s_%s_%s_%s" % (n, s, l, c), parse_epoch(b), parse_epoch(e)

    def _parse_availability(self, response):
        with open(response, 'r') as input:
            availability = None
            for line in input:
                if not line.startswith('#'):
                    sncl, b, e = self._parse_line(line)
                    if availability and not availability.sncl == sncl:
                        yield availability
                        availability = None
                    if not availability:
                        availability = Coverage(self._log, self._timespan_tol, sncl)
                    availability.add_epochs(b, e)
            if availability:
                yield availability

    def _scan_index(self, sncl):
        availability = SingleSNCLBuilder(self._log, self._timespan_tol, sncl)

        def callback(row):
            availability.add_timespans(row[0], row[1])

        try:
            self.foreachrow('''select timespans, samplerate
                                    from tsindex 
                                    where network=? and station=? and location=? and channel=?
                                    order by starttime, endtime''',
                            sncl.split('_'),
                            callback, quiet=True)
        except OperationalError:
            self._log.debug('No index - first time using rover?')
        return availability.coverage()

    def _new_source(self, source, dataselect_url, completion_callback):
        if source in self._sources and self._sources[source].worker_count:
            raise Exception('Cannot overwrite active source %s' % self._sources[source])
        self._sources[source] = Source(source, dataselect_url, completion_callback)
        return self._sources[source]

    def add(self, name, path, availability_url, dataselect_url, completion_callback):
        """
        Add a source and associated coverage, retrieving data from the
        availability service.
        """
        request = self._build_request(path)
        response = self._get_availability(request, availability_url)
        try:
            source = self._new_source(name, dataselect_url, completion_callback)
            for remote in self._parse_availability(response):
                self._log.debug('Available data: %s' % remote)
                local = self._scan_index(remote.sncl)
                self._log.debug('Local data: %s' % local)
                required = remote.subtract(local)
                source.add_coverage(required)
        finally:
            if self._delete_files:
                safe_unlink(request)
                safe_unlink(response)

    # display expected downloads

    def display(self):
        """
        Display a summary of the data that have not been expanded into downloads.
        """
        total_seconds, total_sncls = 0, 0
        print()
        for name in self._sources.keys():
            source = self._sources[name]
            coverages = source.get_coverages()
            if name != DEFAULT_NAME:
                print('  Subscription %s ' % source)
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
            if name != DEFAULT_NAME:
                if source_sncls:
                    print()
                print('  %s: %d SNCLSs; %4.2f sec' % (name, source_sncls, source_seconds))
                print()
        print('  Total: %d SNCLSs; %4.2f sec' % (total_sncls, total_seconds))
        print()
        return total_sncls

    # downloading data and processing in the pipeline

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
            if source.worker_count < c.worker_count:
                return False
        return True

    def _clean_sources(self):
        names = list(self._sources.keys())
        for name in names:
            if self._source(name).is_complete():
                self._log.debug('Source %s complete' % self._source(name))
                del self._sources[name]

    def is_idle(self):
        """
        Are we no longer downloading data?
        """
        self._clean_sources()
        if not self._sources:
            self._update_stats()  # wipe
            return True
        else:
            return False

    def step(self):
        """
        A single iteration of the manager's main loop.  Can be inter-mixed with add_source and add_coverage.
        Cleaning logic assumes coverages for a source are all added at once, though.  If you don't, source
        may be deleted when you don't expect it.
        """
        if not self._config_path:
            raise Exception('DownloadManager was created only to display data (no config_path)')
        self._workers.check()
        self._clean_sources()
        self._update_stats()
        while self._workers.has_space() and self._has_data():
            sources = list(map(lambda name: self._source(name), sorted(self._sources.keys())))
            while True:
                source = self._next_source(sources)
                if self._has_least_workers(source): break
            if source.has_days():
                source.new_worker(self._log, self._workers, self._config_path, self._rover_cmd)
                self._n_downloads += 1
            self._clean_sources()

    def download(self):
        """
        Run to completion (for a single shot, after add()).
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

    # stats for web display

    def _create_stats_table(self):
        self.execute('''create table if not exists rover_download_stats (
                          submission text not null,
                          initial_coverages int not null,
                          remaining_coverages int not null,
                          initial_time float not null,
                          remaining_time float not null
                        )''')

    def _update_stats(self):
        with self._db:  # single transaction
            self._db.cursor().execute('begin')
            self._db.execute('delete from rover_download_stats', tuple())
            for source in self._sources.values():
                stats = source.stats()
                self._db.execute('''insert into rover_download_stats
                                      (submission, initial_coverages, remaining_coverages, initial_time, remaining_time)
                                      values (?, ?, ?, ?, ?)''',
                                 (source.name, source.initial_stats[0], stats[0], source.initial_stats[1], stats[1]))

    def _start_web(self):
        # don't use shell so PPID is us
        cmd = self._rover_cmd.split(' ')
        cmd.append(WEB)
        cmd.extend(['-f', self._config_path])
        cmd.extend([mm(VERBOSITY), '0'])
        self._log.debug('Starting web: %s' % cmd)
        Popen(cmd, shell=False, stdin=None, stdout=None, stderr=None, close_fds=True)
