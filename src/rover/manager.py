import datetime as dt
from collections import deque
from random import randint
from sqlite3 import OperationalError
from time import time, sleep

from .args import mm, FORCEFAILURES, DELETEFILES, TEMPDIR, HTTPTIMEOUT, HTTPRETRIES, TIMESPANTOL, DOWNLOADRETRIES, \
    DOWNLOADWORKERS, ROVERCMD, MSEEDINDEXCMD, LOGUNIQUE, LOGVERBOSITY, VERBOSITY, DOWNLOAD, DEV, WEB, SORTINPYTHON, \
    TIMESPANINC, ABORT_CODE
from .config import write_config
from .coverage import Coverage, SingleSNCLBuilder
from .download import DEFAULT_NAME, TMPREQUEST, TMPRESPONSE
from .sqlite import SqliteSupport
from .utils import utc, EPOCH_UTC, PushBackIterator, format_epoch, safe_unlink, unique_path, post_to_file, \
    sort_file_inplace, parse_epoch, check_cmd, run, windows, diagnose_error, format_year_day_epoch
from .workers import Workers

"""
The core logic for scheduling multiple downloads.  Called by both the daemon and `rover retrieve`.
"""


class ManagerException(Exception):
    """
    Separate class so we can avoid sending additional emails when manager fails.
    """


class ProgressStatistics:
    """
    Encapsulate the statistics that measure progress for a single retrieval.
    Statistics are pairs of values:
      index 0 - current value
      index 1 - initial value / limit
    """

    download_bytes = 0 # number of downloaded bytes per run
    download_total_bytes = 0 # total number of downloaded bytes
    download_retry_count = 1 # number of times that tried to download

    def __init__(self):
        self.__prev_net_sta = [None, None]
        self.stations = [0, 0]
        self.seconds = [0, 0]
        self.chunks = [0, 0]

    def add_coverage(self, coverage):
        net_sta = coverage.sncl.split('_')[0:2]
        if net_sta != self.__prev_net_sta:
            self.stations[1] += 1
            self.__prev_net_sta = net_sta
        # but seconds are counted either way
        for start, end in coverage.timespans:
            self.seconds[1] += (end - start)

    def pop_timespan(self, start, end):
        self.seconds[0] += (end - start)

    def add_chunks(self, n):
        self.stations[0] += 1  # a set of chunks is for a single station
        # the day count isn't global - it's per sncl (coverage) - so resets
        self.chunks[0] = 0
        self.chunks[1] = n

    def pop_chunk(self):
        self.chunks[0] += 1

    def __str__(self):
        return '(N_S %d/%d; day %d/%d)' % (self.stations[0], self.stations[1], self.chunks[0], self.chunks[1])


class ErrorStatistics:
    """
    Encapsulate the statistics that count errors.
    Raw values are per retrieval, they are accumulated on the source.
    """
    def __init__(self):
        self.downloads = 0
        self.errors = 0
        self.final_errors = None

    def accumulate(self, errors):
        self.downloads += errors.downloads
        self.errors += errors.errors
        self.final_errors = errors.errors


class Chunks:
    """
    A chunk is a collection of SNCLs and timespans that are downloaded at once.
    We used to download each individually, but that required too many parallel requests to
    be efficient, so now we collect them here.
    This is a *collection* of chunks because a single chunk is only for one calendar day -
    we may assemble multiple days when moving from the coverages to chunks.
    """

    def __init__(self, temp_dir):
        self.__temp_dir = temp_dir
        self.__chunks = {}   # list of (sncl, start, end) indexed by end of day epoch
        self.__network = None
        self.__station = None

    def __bool__(self):
        return bool(self.__chunks)

    def __len__(self):
        return len(self.__chunks)

    @staticmethod
    def _end_of_day(epoch):
        day = dt.datetime.fromtimestamp(epoch, utc)
        right = (dt.datetime(day.year, day.month, day.day, tzinfo=utc)
                 + dt.timedelta(hours=24) - EPOCH_UTC).total_seconds()
        left = right - 0.000001
        return left, right

    def _append(self, right, sncl, start, end):
        if right not in self.__chunks:
            self.__chunks[right] = []
        self.__chunks[right].append((sncl, start, end))

    def _set_ns(self, sncl):
        nslc = sncl.split('_')
        self.__network = nslc[0]
        self.__station = nslc[1]

    def sncl_ok(self, sncl):
        nslc = sncl.split('_')
        return not self.__chunks or (nslc[0] == self.__network and nslc[1] == self.__station)

    def add_coverage(self, coverage):
        sncl, timespans = coverage.sncl, PushBackIterator(iter(coverage.timespans))
        if not self.__chunks:
            self._set_ns(sncl)

        # Determine sampling period (interval)
        # On initial download we do not know the sampling rate/period, but if data exists locally we do
        # This indicates that data bounds are determined from local data
        try:
            sampleperiod = 1 / coverage.samplerate
        except:
            sampleperiod = None

        for start, end in timespans:
            left, right = self._end_of_day(start)

            # If end time is before end of day, append whole range.
            if right > end:
                # Skip if max request would be smaller than sample period, if known (implying local data bounds)
                # In this case, assuming the sampling interval is regular, no data is expected
                if sampleperiod and sampleperiod > 0 and (left - start) < sampleperiod:
                    continue
                else:
                    self._append(right, sncl, start, end)

            # Otherwise, add the range beyond the current day to the timespans and
            # append the range that fits in the first day
            else:
                timespans.push((right, max(end, right)))

                # Skip if max request would be smaller than sample period, if known (implying local data bounds)
                # In this case, assuming the sampling interval is regular, no data is expected
                if sampleperiod and sampleperiod > 0 and (left - start) < sampleperiod:
                    continue
                else:
                    self._append(right, sncl, start, left)


    @staticmethod
    def format_sncl(sncl):
        return ' '.join(code if code else '--' for code in sncl.split('_'))

    def pop(self, progress):
        right = next(iter(sorted(self.__chunks.keys())))
        description = '%s_%s %s' % (self.__network, self.__station, format_year_day_epoch(right-24*3600))
        data = self.__chunks[right]
        path = unique_path(self.__temp_dir, 'rover_chunk', description)
        with open(path, 'w') as out:
            for (sncl, start, end) in data:
                progress.pop_timespan(start, end)
                print('%s %s %s' % (self.format_sncl(sncl), format_epoch(start), format_epoch(end)), file=out)
        del self.__chunks[right]
        progress.pop_chunk()
        return description, path


class Retrieval:
    """
    A single attempt at downloading data for a subscription or retrieval
    (some care is taken here to avoid large files in memory - the list of downloads is generated
    on the fly).
    """

    def __init__(self, log, name, temp_dir, delete_files, dataselect_url, force_failures):
        self._log = log
        self._name = name
        self._temp_dir = temp_dir
        self._delete_files = delete_files
        self._dataselect_url = dataselect_url
        self._force_failures = force_failures
        self._coverages = deque()  # fifo: appendright / popleft; exposed for display
        self._chunks = None
        self.worker_count = 0
        self.errors = ErrorStatistics()
        self.progress = ProgressStatistics()

    def add_coverage(self, coverage):
        """
        Add a coverage to retrieve.
        """
        if coverage:  # this avoids us showing more stations to download than are downloaded
            self._coverages.append(coverage)
            self.progress.add_coverage(coverage)

    def get_coverages(self):
        """
        Provide access to coverages (for listing)
        """
        return list(self._coverages)

    def has_chunks(self):
        """
        Ensure chunks has some data, if possible, and return whether it has any.
        """
        if self._chunks:
            return True
        self._chunks = Chunks(self._temp_dir)
        while self._coverages and self._chunks.sncl_ok(self._coverages[0].sncl):
            self._chunks.add_coverage(self._coverages.popleft())
        if self._chunks:
            self.progress.add_chunks(len(self._chunks))
            return True
        return False

    def _build_url(self, sncl, start, end):
        url_params = 'net=%s&sta=%s&loc=%s&cha=%s' % \
                     tuple(code if code else '--' for code in tuple(sncl.split('_')))
        return '%s?%s&start=%s&end=%s' % (self._dataselect_url, url_params, format_epoch(start), format_epoch(end))

    def _worker_callback(self, command, return_code, path, **kwargs):
        feedback = kwargs.get("feedback")
        if feedback:
            bytecount = feedback.get("download_byte_count", 0)
            ProgressStatistics.download_bytes += bytecount
            ProgressStatistics.download_total_bytes += bytecount
        if self._delete_files:
            safe_unlink(path)
        self.worker_count -= 1
        self.errors.downloads += 1
        if return_code:
            self.errors.errors += 1
            if return_code != ABORT_CODE:   # hide message on ctrl-C as we will exit as well
                self._log.error('Download %s failed (return code %d)' % (self._name, return_code))

    def new_worker(self, workers, config_path, rover_cmd):
        """
        Launch a new worker (called by manager main loop).
        """
        description, path = self._chunks.pop(self.progress)
        self._log.default('Downloading %s %s' % (description, self.progress))
        # for testing error handling we can inject random errors here
        if randint(1, 100) <= self._force_failures:
            self._log.warn('Random failure expected (%s %d)' % (mm(FORCEFAILURES), self._force_failures))
            command = 'exit 1  # failure for tests'
        else:
            # we only pass arguments on the command line that are different from the
            # default (which is in the file)
            if windows():
                command = 'pythonw -m rover -f %s %s "%s"' % (config_path, DOWNLOAD, path)
            else:
                command = '%s -f %s %s "%s"' % (rover_cmd, config_path, DOWNLOAD, path)
        self._log.debug(command)

        callback_function = lambda cmd, rtn, **kwargs: self._worker_callback(cmd, rtn, path, **kwargs)

        try:
            workers.execute(command, callback=callback_function, feedback=True)
        except Exception as ex:
            self._log.error('Worker failed (%s): %s' % (command, ex))
        else:
            self.worker_count += 1

    def is_complete(self):
        """
        Is this retrieval complete?
        """
        return self.worker_count == 0 and not self.has_chunks()


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

    def __init__(self, config, name, fetch, request_path, availability_url, dataselect_url, completion_callback):
        super().__init__(config)
        self._log = config.log
        self._force_failures = config.arg(FORCEFAILURES)
        self._delete_files = config.arg(DELETEFILES)
        self._temp_dir = config.dir(TEMPDIR)
        self._http_timeout = config.arg(HTTPTIMEOUT)
        self._http_retries = config.arg(HTTPRETRIES)
        self._timespan_inc = config.arg(TIMESPANINC)
        self._timespan_tol = config.arg(TIMESPANTOL)
        self._config = config
        self.download_retries = config.arg(DOWNLOADRETRIES)
        self._sort_in_python = config.arg(SORTINPYTHON)
        self.name = name
        self._request_path = request_path
        self._availability_url = availability_url
        self._dataselect_url = dataselect_url
        self._completion_callback = completion_callback
        self.n_retries = 0
        self._retrieval = None
        self.start_epoch = time()
        self.errors = ErrorStatistics()
        self._expect_empty = False
        self.consistent = UNCERTAIN
        # load first retrieval immediately so we don't print messages in the middle of list-retrieve
        self._new_retrieval(fetch)
        self.initial_progress = self._retrieval.progress

    def __str__(self):
        return '%s (%s)' % (self.name, self._dataselect_url)

    def get_coverages(self):
        """
        Provide access to coverages (for listing)
        """
        return self._retrieval.get_coverages()

    def stats(self):
        """
        Provide access to latest stats (for reporting).
        """
        return self._retrieval.progress

    def has_chunks(self):
        """
        Does retrieval have data?
        """
        return self._retrieval.has_chunks()

    @property
    def worker_count(self):
        """
        Number of workers being used.
        """
        return self._retrieval.worker_count

    def new_worker(self, workers, config_path, rover_cmd):
        """
        Launch a new worker (called by manager main loop).
        """
        self._retrieval.new_worker(workers, config_path, rover_cmd)

    @property
    def _name(self):
        """
        Name for log messages - empty string for retrieve, otherwise identifies subscription.
        """
        # don't mention subscriptions when called from `rover retrieve`
        return '' if self.name == DEFAULT_NAME else 'subscription %s ' % self.name

    def is_complete(self):
        """
        Is this source complete (all retrievals)?
        Dependent Functions:
        
        is_complete_final_read: Verifies that all data is downloaded with no errors makes ROVER robust. 
        If data is missing _new_retrieval and _is_complete_initial_reads are called.
        _is_complete_initial_reads: Call the new_retrieval function until all data is downloaded with no errors. 
        _new_retrieval: 
        
        important variables: 

        self._expect_empty: Determines if the _is_complete_final_read or _is_complete_initial_reads function is called/
        complete: Terminates the loop.
        """
        retry_possible = self.n_retries < self.download_retries

        # Only one possible rety needs to be written in the intial loop.
        # The second loop is just there to verfy the first loop.
        # The total possible retries need to counted upward in the first and second loop

        # this is complicated by the fact that we also check for consistency.
        # inconsistency is when we expect to download no data, but still get some, or expect to get
        # some, but get nothing.  we can't detect all cases, but we do our best by waiting until
        # we get a clean download (no errors and so presumably complete) and then running an
        # extra download.  that should generate no downloads.  if it doesn't, we have problems.

        # the default value for consistent is UNCERTAIN so it is left unchanged in many places below
        # we throw an exception if we finish with incomplete data (errors) or proof of inconsistency.
        if self._retrieval.is_complete():
            self.errors.accumulate(self._retrieval.errors)
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
        if self._retrieval.errors.errors:

            # if we can retry, then do so
            if retry_possible:
                self._log.default(('Retrieval attempt %d of %d completed with %d errors. '+
                                    'We will retry to check that all data were retrieved') %
                                    (self.n_retries, self.download_retries, self._retrieval.errors.errors))
                self._new_retrieval(True)
                return False
            # otherwise, we can't retry so we're done, but failed.
            else:
                raise ManagerException('Retrieval attempt %d of %d had %d errors on the final attempt.' %
                                       (self.n_retries, self.download_retries, self._retrieval.errors.errors))

        # No errors last retrieval, but we did attempt some downloads
        # If these boolean conditions are maintained then rover will continue to make download attmepts.
        elif self._retrieval.errors.downloads:
            # Can we try again, to make sure there are no more data retrievable?
            # Deal with the case when config has number of download attempts set to 1.
            if self.download_retries == 1:
                if retry_possible:

                    self._log.default(('Retrieval attempt %d of %d had no errors and we downloaded data.'
                                       'The config parameter download-retries is set to %d attempt so rover is exiting.'
                                       'We recommend increasing the number of download attempts. ')
                                      % (self.n_retries, self.download_retries, self.download_retries))
                    self._expect_empty = True
                    return True
            else:
                if ProgressStatistics.download_bytes > 0: # Determines if data was collected.
                    if ProgressStatistics.download_retry_count < 100: # A hard limit on the amount of times we will attempt to download a request
                        self._log.default('Successful retrieval, downloaded data so resetting retry count and verify.')
                        self.n_retries = self.n_retries - 1
                        self._expect_empty = False
                        self._new_retrieval(True)
                        ProgressStatistics.download_bytes = 0
                        ProgressStatistics.download_retry_count += 1
                        return False
                    else :
                        self._log.default(('The retrieval has been attempted %d times. ROVER is exiting. Please check the log files and try again later.')
                                          % (ProgressStatistics.download_retry_count))
                        self._expect_empty =True
                        return True
                elif retry_possible:
                    self._log.default(('Successful retrieval attempt %d of %d, but no new data downloaded so try again.')
                                      % (self.n_retries, self.download_retries))

                    self._expect_empty =False
                    self._new_retrieval(True)
                    return False
                # if not, we're going to say we're complete anyway, since we didn't have any errors.
                else:
                    self._log.default(
                        ('The latest retrieval attempt had no errors.  Stopping at %d retry attempts.') % (self.n_retries))
                    self._expect_empty =True
                    return False

        # no errors and no data. used for rovers first download attempt and to exit out the
        # _is_complete_initial_reads program so the _is_complete_final_reads program can be run.
        # When escaping is_complete_initial_reads an additional _new_retrieval should not be run.
        else:
            # presumably this was an empty initial download
            if self.n_retries == 1:
                # can we try again to make sure things are consistent?
                if retry_possible:
                    self._log.default('The initial retrieval attempt resulted in no errors or data downloaded, will verify.')
                    self._expect_empty = True
                    self._new_retrieval(True)

                    return False
                # if not, we're going to say we're complete anyway.
                else:
                    self._log.default('The initial retrieval attempt had no errors and no retries are configured.')
                    return True
            # something odd has happened - no data when it wasn't expected
            else:
                # can we try again to make sure things are consistent?
                if retry_possible:
                    self._log.default(('Retrieval attempt %d of %d had no errors and downloaded no data. ' +
                                       'We will check that all data were retrieved.') % (self.n_retries, self.download_retries))
                    self._expect_empty = True
                    return False
                else:
                    self.consistent = INCONSISTENT
                    raise ManagerException(('The final retrieval, attempt %d of %d, downloaded no data' +
                                            'following an earlier error (inconsistent web services?)') %
                                           (self.n_retries, self.download_retries))

    def _is_complete_final_read(self, retry_possible):

        # the last retrieval had errors (it shouldn't have - we should be on final empty download)
        if self._retrieval.errors.errors:
            self.consistent = INCONSISTENT
            # if we can retry, then do so
            if retry_possible:
                self._log.default(('The latest retrieval attempt had %d errors after %d attempts.  ' +
                                   'We will retry to complete the retrieval.') %
                                  (self._retrieval.errors.errors, self.n_retries))
                self._new_retrieval(True)
                self._expect_empty = False
                return False
            # otherwise, we can't retry so we're done, but failed.
            else:
                raise ManagerException('The latest retrieval attempt had %d errors on final attempt (%d of %d).' %
                                       (self._retrieval.errors.errors, self.n_retries, self.download_retries))

        # no errors last retrieval, but we did download some more data (again, unexpected)
        elif self._retrieval.errors.downloads:
            # special case where we had no sample interval until first request, so second request
            # got a single point that was missed because the interval was too small for the server
            if self.n_retries == 2:
                if retry_possible:
                    self._log.default(('The latest retrieval attempt downloaded additional data - ' +
                                       'probably an isolated point that was not retrieved on the first pass. ' +
                                       'We will retry to make sure data are complete.'))
                    self._new_retrieval(True)
                    self._expect_empty = False
                    return False
                else:
                    self._log.default(('The latest retrieval attempt downloaded additional data - ' +
                                       'probably an isolated point that was not retrieved on the first pass. ' +
                                       'We cannot be certain download is complete without more retries.'))
                    return True
            else:
                self.consistent = INCONSISTENT
                # can we try again, in case this was some weird hiccup?
                # there's a case where this is expected - when we have data on a day boundary and need tp
                # download once to get the samplerate so we can judge exactly how small a chunk to take
                # from the next day.
                if retry_possible:
                    self._log.default(('The latest retrieval attempt downloaded unexpected data so trying again ' +
                                       'to check behavior.'))
                    self._new_retrieval(True)
                    self._expect_empty = False
                    return False
                # something odd is happening
                else:
                    raise ManagerException(('The previous %d retrieval attempts could not download some '+
                                            'requested data available at the data center. Consider running'+
                                            ' `rover list-retrieve` to determine missing data.') %
                                           (self.n_retries))

        # no errors and no data
        else:
            self.consistent = CONFIRMED
            self._log.default('The final %sretrieval, attempt %d of %d, made no downloads and had no errors, we are complete.' %
                              (self._name, self.n_retries, self.download_retries))
            return True

    def _new_retrieval(self, fetch):
        # fetch indicates we're not simply querying and so should check for no data and prime days
        self.n_retries += 1
        if fetch:
            self._log.default('Trying new %sretrieval attempt %d of %d.' %
                              (self._name, self.n_retries, self.download_retries))
        self._retrieval = Retrieval(self._log, self._name, self._temp_dir, self._delete_files,
                                    self._dataselect_url, self._force_failures)
        request = self._build_request(self._request_path)
        response = self._get_availability(request, self._availability_url)
        try:
            # compare database and availability to construct list of missing data
            # we could make this lazy, but then we lose progression statistics.  so
            # just try to be as meagre with memory use as possible.
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
        if fetch and not self._retrieval.has_chunks():
            self._log.default('%sRetrieval attempt %d of %d is complete.' %
                              (self._name, self.n_retries, self.download_retries))

    def _build_request(self, path):
        tmp = unique_path(self._temp_dir, TMPREQUEST, path)
        self._log.debug('Prepending options to %s via %s' % (path, tmp))
        with open(tmp, 'w') as output:
            print('merge=samplerate,quality', file=output)
            with open(path, 'r') as inpath:
                for line in inpath:
                    print(line, file=output, end='')
        return tmp

    def _get_availability(self, request, availability_url):
        self._log.info('Checking availability service')
        response = unique_path(self._temp_dir, TMPRESPONSE, request)
        response, check_status = post_to_file(availability_url, request, response, self._http_timeout, self._http_retries, self._log)
        try:
            check_status()
            return response
        except Exception as e:
            diagnose_error(self._log, str(e), request, response)
            raise

    def _parse_line(self, line):
        try:
            n, s, l, c, b, e = ('' if token == '--' else token for token in line.split())
            return "%s_%s_%s_%s" % (n, s, l, c), parse_epoch(b), parse_epoch(e)
        except:
            raise Exception('Could not parse "%s" in the response from the availability service' % line)

    def _parse_availability(self, response):
        try:
            if response is not None:  # None when no data returned
                sort_file_inplace(self._log, response, self._temp_dir, self._sort_in_python)
                with open(response, 'r') as input:
                    availability = None
                    for line in input:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            sncl, b, e = self._parse_line(line)
                            if availability and not availability.sncl == sncl:
                                yield availability
                                availability = None
                            if not availability:
                                availability = Coverage(self._log, self._timespan_tol, self._timespan_inc, sncl)
                            availability.add_epochs(b, e)
                    if availability:
                        yield availability
        except Exception as e:
            diagnose_error(self._log, 'Problems parsing the availability service response.',
                           self._request_path, response)
            raise

    def _scan_index(self, sncl):
        availability = SingleSNCLBuilder(self._log, self._timespan_tol, self._timespan_inc, sncl)

        def callback(row):
            availability.add_timespans(row[0], row[1])

        try:
            # coalesce below replaces [...] with <...> based on start/endtime if timespans is missing
            # this is handled by rover.coverage.BaseBuilder
            # see issue 47
            # note we separate times with space as time contains colons
            self.foreachrow('''SELECT coalesce(timespans, '<' || starttime || ' ' || endtime || '>'), samplerate
                                    FROM tsindex
                                    WHERE network=? AND station=? AND location=? AND channel=?
                                    ORDER BY starttime, endtime''',
                            sncl.split('_'),
                            callback, quiet=True)
        except OperationalError:
            self._log.debug('No index - check rover.config')
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

    def add(self, name, request_path, fetch, availability_url, dataselect_url, completion_callback):
        # fetch is necessary here because source wants to prime days for retrieval
        if name in self._sources and self._sources[name].worker_count:
            raise Exception('Cannot overwrite active source %s' % self._sources[name])
        self._sources[name] = Source(self._config, name, fetch, request_path, availability_url, dataselect_url,
                                     completion_callback)

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
                for (start, end) in coverage.timespans:
                    seconds = end - start
                    sncl_seconds += seconds
                    source_seconds += seconds
                    total_seconds += seconds
                source_sncls += 1
                total_sncls += 1
                print('  %s  (%4.2f sec)' % (coverage.sncl, sncl_seconds))
                for (start, end) in coverage.timespans:
                    print('    %s - %s  (%4.2f sec)' % (format_epoch(start), format_epoch(end), end - start))
            if name != DEFAULT_NAME:
                if source_sncls:
                    print()
                print('  %s: %d N_S_L_C; %4.2f sec' % (name, source_sncls, source_seconds))
                print()
        print('  Total: %d N_S_L_C; %4.2f sec' % (total_sncls, total_seconds))
        print()
        return total_sncls

    # downloading data and processing in the pipeline

    def _has_data(self):
        for source in self._sources.values():
            if source.has_chunks():
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
                    raise
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

    # the step method below is probably the best place to insert a call to execute
    # pragma wal_checkpoint if we have further problems with locked databases.
    # the idea would be to add a counter to the manager and every 1000 (say) calls,
    # wait for all workers to close and then execute the pragma.  this would
    # allow the database to update without contention.

    # we would also need to disable automatic checkpointing with pragma
    # wal_autocheckpoint and make sure to run a checkpoint on count 0 (ie at the start).

    def step(self, quiet=True):
        """
        A single iteration of the manager's main loop.  Can be inter-mixed with add().
        """
        # the logic here is a little opaque because we need to mix layers of abstraction to
        # get the fine control we want for load balancing - we want to give jobs to whichever
        # source has least threads running so that the total number of workers (and so total
        # download bandwidth) is evenly spread across all servers.
        # a consequence of that is that there's no "step()" for lower levels.  this is also
        # partly because all the work is done in a separate worker process.  instead, most of
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
            if source.has_chunks():
                source.new_worker(self._workers, self._config_path, self._rover_cmd)
                self._n_downloads += 1
            # todo - does this do anything useful without a workers.check()?
            self._clean_sources(quiet=quiet)

    def download(self):
        """
        Run to completion (for a single shot, after add()).
        """
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
        self.execute('''CREATE TABLE IF NOT EXISTS rover_download_stats (
                          submission text not null,
                          initial_stations int not null,
                          remaining_stations int not null,
                          initial_time float not null,
                          remaining_time float not null,
                          n_retries int not null,
                          download_retries int not null
                        )''')

    def _update_stats(self):
        with self._db:  # single transaction
            self._db.cursor().execute('BEGIN')
            self._db.execute('DELETE FROM rover_download_stats', tuple())
            for source in self._sources.values():
                progress = source.stats()
                self._db.execute('''INSERT INTO rover_download_stats
                                    (submission, initial_stations, remaining_stations, initial_time, remaining_time,
                                     n_retries, download_retries)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                 (source.name,
                                  progress.stations[1], progress.stations[1] - progress.stations[0],
                                  progress.seconds[1], max(0, int(progress.seconds[1] - progress.seconds[0])),
                                  source.n_retries, source.download_retries))

    def _start_web(self):
        if windows():
            cmd = 'pythonw -m rover %s -f %s %s 0' % (WEB, self._config_path, mm(VERBOSITY))
        else:
            cmd = '%s %s -f %s %s 0' % (self._rover_cmd, WEB, self._config_path, mm(VERBOSITY))
        run(cmd, self._log, uncouple=True)
