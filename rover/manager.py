
import datetime as dt
from collections import deque
from random import randint
from sqlite3 import OperationalError
from subprocess import Popen
from time import time, sleep

from .args import mm, FORCEFAILURES, DELETEFILES, TEMPDIR, HTTPTIMEOUT, HTTPRETRIES, TIMESPANTOL, DOWNLOADRETRIES, \
    DOWNLOADWORKERS, ROVERCMD, MSEEDINDEXCMD, LOGUNIQUE, LOGVERBOSITY, VERBOSITY, DOWNLOAD, DEV, WEB
from .config import write_config
from .coverage import Coverage, SingleSNCLBuilder
from .download import DEFAULT_NAME, TMPREQUEST, TMPRESPONSE
from .sqlite import SqliteSupport
from .utils import utc, EPOCH_UTC, PushBackIterator, format_epoch, safe_unlink, unique_path, post_to_file, \
    sort_file_inplace, parse_epoch, check_cmd
from .workers import Workers


"""
The core logic for scheduling multiple downloads.  Called by both the daemon and `rover retrieve`.
"""


class Retrieval:
    """
    A single attempt at downloading data for a subscription or retrieval
    (some care is taken here to avoid large files in memory - the list of downloads is generated
    on the fly).
    """

    def __init__(self, log, name, dataselect_url, force_failures):
        self._log = log
        self._name = name
        self._dataselect_url = dataselect_url
        self._force_failures = force_failures
        self._coverages = deque()  # fifo: appendright / popleft; exposed for display
        self._days = deque()  # fifo: appendright / popleft
        self.worker_count = 0
        self.n_downloads = 0
        self.n_errors = 0

    def add_coverage(self, coverage):
        self._coverages.append(coverage)

    def get_coverages(self):
        return list(self._coverages)

    @staticmethod
    def _end_of_day(epoch):
        day = dt.datetime.fromtimestamp(epoch, utc)
        right = (dt.datetime(day.year, day.month, day.day, tzinfo=utc)
                 + dt.timedelta(hours=24) - EPOCH_UTC).total_seconds()
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
            self._log.error('Download %sfailed (return code %d)' % (self._name, return_code))

    def new_worker(self, workers, config_path, rover_cmd):
        # this is where the real work is done, and it's called from the manager.
        url = self._build_url(*self._days.popleft())
        # for testing error handling we can inject random errors here
        if randint(1, 100) <= self._force_failures:
            self._log.warn('Random failure expected (%s %d)' % (mm(FORCEFAILURES), self._force_failures))
            command = 'exit 1  # failure for tests'
        else:
            # we only pass arguments on the command line that are different from the
            # default (which is in the file)
            command = '%s -f \'%s\' %s \'%s\'' % (rover_cmd, config_path, DOWNLOAD, url)
        self._log.debug(command)
        workers.execute(command, self._worker_callback)
        self.worker_count += 1

    def is_complete(self):
        return self.worker_count == 0 and not self.has_days()


# avoid enum because python2 doesn't have it and we want code that runs on both
# (if we use backports then it's a conditional install)
UNCERTAIN, CONFIRMED, INCONSISTENT = 0, 1, 2


class Source(SqliteSupport):
    """
    Data for a single source in the download manager.
    """

    # this has two jobs, really.
    # first, it runs retrievers as often as required.  this is the "main loop" logic from the
    # rfq and was added later in the project (before we failed and reported).
    # second. it collects and reports statistics that are used by the download manager and displayed to the user.
    # these are the public attributes and properties (delegated to the current retriever).

    def __init__(self, config, name, request_path, availability_url, dataselect_url, completion_callback):
        super().__init__(config)
        self._log = config.log
        self._force_failures = config.arg(FORCEFAILURES)
        self._delete_files = config.arg(DELETEFILES)
        self._temp_dir = config.dir(TEMPDIR)
        self._http_timeout = config.arg(HTTPTIMEOUT)
        self._http_retries = config.arg(HTTPRETRIES)
        self._timespan_tol = config.arg(TIMESPANTOL)
        self.download_retries = config.arg(DOWNLOADRETRIES)
        self.name = name
        self._request_path = request_path
        self._availability_url = availability_url
        self._dataselect_url = dataselect_url
        self._completion_callback = completion_callback
        self.n_retries = 0
        self._retrieval = None
        self.start_epoch = time()
        self.n_downloads = 0
        self.n_errors = 0
        self.n_final_errors = None
        self._expect_empty = False
        self.consistent = UNCERTAIN
        # load first retrieval immediately so we don't print messages in the middle of list-retrieve
        self._new_retrieval()
        self.initial_stats = self._retrieval.stats()

    def __str__(self):
        return '%s (%s)' % (self.name, self._dataselect_url)

    def get_coverages(self):
        return self._retrieval.get_coverages()

    def stats(self):
        return self._retrieval.stats()

    def has_days(self):
        return self._retrieval.has_days()

    @property
    def worker_count(self):
        return self._retrieval.worker_count

    def new_worker(self, workers, config_path, rover_cmd):
        self._retrieval.new_worker(workers, config_path, rover_cmd)

    @property
    def _name(self):
        """
        Name for log messages - empty string for retrieve, otherwise identifies subscription.
        """
        # don't mention subscriptions when called from `rover retrieve`
        return '' if self.name == DEFAULT_NAME else 'subscription %s ' % self.name

    def is_complete(self):

        retry_possible = self.n_retries < self.download_retries

        # this is complicated by the fact that we also check for consistency.
        # inconsistency is when we expect to download no data, but still get some, or expect to get
        # some, but get nothing.  we can't detect all cases, but we do our best by waiting until
        # we get a clean download (no errors and so presumably complete) and then running an
        # extra download.  that should generate no downloads.  if it doesn't, we have problems.

        # that sounds fairly simple, but when you consider all possible cases you get the code below...

        # the default value for consistent is UNCERTAIN so it is left unchanged in many places below
        # we throw an exception if we finish with incomplete data (errors) or proof of inconsistency.

        if self._retrieval.is_complete():

            # update public stats
            self.n_downloads += self._retrieval.n_downloads
            self.n_errors += self._retrieval.n_errors
            self.n_final_errors = self._retrieval.n_errors

            complete = True  # default if exception thrown
            try:
                if self._expect_empty:
                    complete = self._is_complete_final_read(retry_possible)
                else:
                    complete = self._is_complete_initial_reads(retry_possible)
                return complete
            finally:
                if complete:
                    self._completion_callback(self)
        else:
            # the current retrieval isn't complete, so we're certainly not done
            return False

    def _is_complete_initial_reads(self, retry_possible):

        # the last retrieval had errors.
        if self._retrieval.n_errors:
            # if we can retry, then do so
            if retry_possible:
                self._log.info('Latest %sretrieval had %d errors; retrying at %d attempts' %
                               (self._name, self._retrieval.n_errors, self.n_retries))
                self._new_retrieval()
                return False
            # otherwise, we can't retry so we're done, but failed.
            else:
                raise Exception('Latest %sretrieval had %d errors on final attempt (of %d)' %
                                (self._name, self._retrieval.n_errors, self.download_retries))

        # no errors last retrieval, but we did download some more data
        elif self._retrieval.n_downloads:
            # can we try again, to make sure there are no more data?
            if retry_possible:
                self._log.info('Latest %sretrieval had no errors, but downloaded data so trying again' % self._name)
                self._expect_empty = True
                self._new_retrieval()
                return False
            # if not, we're going to say we're complete anyway, since we didn't have any errors.
            else:
                self._log.info(
                    'Latest %sretrieval had no errors, but downloaded data; no retry as already made %d attempts'
                    % (self._name, self.n_retries))
                return True

        # no errors and no data
        else:
            # presumably this was an empty initial download
            if self.n_retries == 1:
                # can we try again to make sure things are consistent?
                if retry_possible:
                    self._expect_empty = True
                    self._log.info('Initial %sretrieval had no errors or data, but retry to check consistency' %
                                   self._name)
                    self._new_retrieval()
                    return False
                # if not, we're going to say we're complete anyway.
                else:
                    self._log.info('Initial %sretrieval had no errors and no retries configured' % self._name)
                    return True
            # something odd has happened - no data when it wasn't expected
            else:
                # can we try again to make sure things are consistent?
                if retry_possible:
                    self._expect_empty = True
                    self._log.info('Latest %sretrieval had no errors or data, but retry to check consistency' %
                                   self._name)
                    self._new_retrieval()
                    return False
                else:
                    self.consistent = INCONSISTENT
                    raise Exception(('Latest %sretrieval downloaded no data on final attempt (of %d) ' +
                                     'following error (inconsistent web services?)') %
                                    (self._name, self.download_retries))

    def _is_complete_final_read(self, retry_possible):

        # the last retrieval had errors (it shouldn't have - we should be on final empty download)
        if self._retrieval.n_errors:
            self.consistent = INCONSISTENT
            # if we can retry, then do so
            if retry_possible:
                self._log.info('Final %sretrieval had %d errors; retrying at %d attempts' %
                               (self._name, self._retrieval.n_errors, self.n_retries))
                self._new_retrieval()
                return False
            # otherwise, we can't retry so we're done, but failed.
            else:
                raise Exception('Final %sretrieval had %d errors on final attempt (of %d)' %
                                (self._name, self._retrieval.n_errors, self.download_retries))

        # no errors last retrieval, but we did download some more data (again, unexpected)
        elif self._retrieval.n_downloads:
            self.consistent = INCONSISTENT
            # can we try again, in case this was some weird hiccup?
            if retry_possible:
                self._log.info('Final %sretrieval downloaded unexpected data so trying again' % self._name)
                self._new_retrieval()
                return False
            # something odd is happening
            else:
                raise Exception(('Final %sretrieval downloaded unexpected data (%d) on final attempt (of %d)' +
                                 ' (inconsistent web services?)') %
                                (self._name, self._retrieval.n_downloads, self.download_retries))

        # no errors and no data
        else:
            self.consistent = CONFIRMED
            self._log.info('Final %sretrieval had no downloads and no errors, so complete' % self._name)
            return True

    def _new_retrieval(self):
        self.n_retries += 1
        self._log.info('Trying new %sretrieval (attempt %d of %d)' %
                       (self._name, self.n_retries, self.download_retries))
        self._retrieval = Retrieval(self._log, self._name, self._dataselect_url, self._force_failures)
        request = self._build_request(self._request_path)
        response = self._get_availability(request, self._availability_url)
        try:
            # compare database and availability to construct list of missing data
            for remote in self._parse_availability(response):
                self._log.debug('Available data: %s' % remote)
                local = self._scan_index(remote.sncl)
                self._log.debug('Local data: %s' % local)
                required = remote.subtract(local)
                self._retrieval.add_coverage(required)
        finally:
            if self._delete_files:
                safe_unlink(request)
                safe_unlink(response)

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
        response = post_to_file(availability_url, request, response, self._http_timeout, self._http_retries, self._log)
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
        self._config = config
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

    def add(self, name, request_path, availability_url, dataselect_url, completion_callback):
        if name in self._sources and self._sources[name].worker_count:
            raise Exception('Cannot overwrite active source %s' % self._sources[name])
        self._sources[name] = Source(self._config, name, request_path, availability_url, dataselect_url, completion_callback)

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

    def _clean_sources(self, quiet=True):
        names = list(self._sources.keys())
        for name in names:
            try:
                complete = self._source(name).is_complete()
            except Exception as e:
                if quiet:
                    complete = True
                else:
                    raise e
            if complete:
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

    def step(self, quiet=True):
        """
        A single iteration of the manager's main loop.  Can be inter-mixed with add().
        """
        # the logic here is a little opaque because we need to mix layers of abstraction to
        # get the fine control we want for load balancing - we want to give jobs to whichever
        # source has least threads running so that the total number of workers (and so total
        # download bandwidth) is evenly spread across all servers.
        # a consequence of that is that there's no "step()" for lower levels.  this is also
        # partly because all teh work is done in a separate worker process.  instead, most of
        # the lower level logic is done in clean_sources() which checks and updates the sources
        # appropriately (and, for single shot downloads, where quiet=False, raises an exception
        # on error).
        if not self._config_path:
            raise Exception('DownloadManager was created only to display data (no config_path)')
        # push any results from completed workers back to the sources
        self._workers.check()
        # and then update the state of the sources
        self._clean_sources(quiet=quiet)
        # with that done, update the stats for teh web display
        self._update_stats()
        # before trying to find a suitable candidates for more work...
        while self._workers.has_space() and self._has_data():
            # the order of sources is sorted here so that we round-robin consistently
            # (starting where we left off last time with self._index)
            sources = list(map(lambda name: self._source(name), sorted(self._sources.keys())))
            while True:
                # consider sources in turn
                source = self._next_source(sources)
                # are they deserving of an extra worker?
                if self._has_least_workers(source):
                    break
            # todo - why is this check needed?  shouldn't this always succeed?
            if source.has_days():
                source.new_worker(self._workers, self._config_path, self._rover_cmd)
                self._n_downloads += 1
            # todo - does this do anything useful without a workers.check()?
            self._clean_sources(quiet=quiet)

    def download(self):
        """
        Run to completion (for a single shot, after add()).
        """
        print('download')
        if len(self._sources) != 1:
            raise Exception('download() logic intended for single source (retrieve)')
        source = next(iter(self._sources.values()))
        try:
            while self._sources and not source.is_complete():
                self.step(quiet=False)
                sleep(0.1)
        finally:
            # not needed in normal use, as no workers when no sources, but useful on error
            self._workers.wait_for_all()
        return self._n_downloads

    # stats for web display

    def _create_stats_table(self):
        self.execute('''create table if not exists rover_download_stats (
                          submission text not null,
                          initial_coverages int not null,
                          remaining_coverages int not null,
                          initial_time float not null,
                          remaining_time float not null,
                          n_retries int not null,
                          download_retries int not null
                        )''')

    def _update_stats(self):
        with self._db:  # single transaction
            self._db.cursor().execute('begin')
            self._db.execute('delete from rover_download_stats', tuple())
            for source in self._sources.values():
                stats = source.stats()
                self._db.execute('''insert into rover_download_stats
                                      (submission, initial_coverages, remaining_coverages, initial_time, remaining_time, 
                                       n_retries, download_retries)
                                      values (?, ?, ?, ?, ?, ?, ?)''',
                                 (source.name, source.initial_stats[0], stats[0], source.initial_stats[1], stats[1],
                                  source.n_retries, source.download_retries))

    def _start_web(self):
        # don't use shell so PPID is us
        cmd = self._rover_cmd.split(' ')
        cmd.append(WEB)
        cmd.extend(['-f', self._config_path])
        cmd.extend([mm(VERBOSITY), '0'])
        self._log.debug('Starting web: %s' % cmd)
        Popen(cmd, shell=False, stdin=None, stdout=None, stderr=None, close_fds=True)