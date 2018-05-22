
import datetime
from os import unlink, makedirs
from os.path import exists
from re import match
from shutil import copyfile
from sqlite3 import OperationalError

from .args import RETRIEVE
from .compact import Compacter
from .config import NewConfig
from .coverage import SingleSNCLBuilder, Coverage
from .download import DownloadManager
from .index import Indexer
from .sqlite import SqliteSupport
from .utils import canonify, post_to_file, run, check_cmd, clean_old_files, \
    match_prefixes, check_leap, parse_epoch, SingleUse, unique_path, canonify_dir_and_make, safe_unlink

"""
The 'rover retrieve' command - check for remote data that we don't already have, download it and ingest it.
"""


RETRIEVEFILE = 'rover_retrieve'
EARLY = datetime.datetime(1900, 1, 1)


class BaseRetriever(SqliteSupport, SingleUse):
    """
### Retrieve

    rover retrieve file

    rover retrieve N.S.L.C begin [end]

Compare available data with the local store, then download, ingest and index data.

The file argument should contain a list of SNCLs and timespans, as appropriate for calling an Availability
service (eg http://service.iris.edu/irisws/availability/1/).  Otherwise, if a SNCL and timespan are given, a
(single-line) file will be automatically constructed containing that data.

The list of available data is retrieved from the service and compared with the local index.  Data not
available locally are downloaded and ingested.

In the comparison of available data, maximal timespans across all quality and sample rates are used (so quality
and samplerate information is "merged").

This command also indexes modified data in the store before processing and runs `rover compact --compact-list1
afterwards to check for duplicate data.

##### Significant Parameters

@temp-dir
@availability-url
@dataselect-url
@timespan-tol
@pre-index
@ingest
@compact
@index
@post-compact
@rover-cmd
@mseed-cmd
@mseed-db
@download-workers
@verbosity
@log-dir
@log-name
@log-verbosity

In addition, parameters for sub-commands (download, ingest, index, compact) will be used - see help for those
commands for more details.

##### Examples

    rover retrieve sncls.txt

will download, ingest, and index any data missing from the local store that are present in the given file.

    rover retrieve IU.ANMO.00.BH1 2017-01-01 2017-01-04

will download, ingest and index and data for IU.ANMO.00.BH1 between the given dates that are missing from the local
store.

"""

    def __init__(self, config):
        SqliteSupport.__init__(self, config)
        SingleUse.__init__(self)
        args = config.args
        self._download_manager = DownloadManager(config)
        self._temp_dir = canonify_dir_and_make(args.temp_dir)
        self._availability_url = args.availability_url
        self._timespan_tol = args.timespan_tol
        self._pre_index = args.pre_index
        self._post_compact = args.post_compact
        # check these so we fail early
        check_cmd('%s -h' % args.rover_cmd, 'rover', 'rover-cmd', self._log)
        check_cmd('%s -h' % args.mseed_cmd, 'mseedindex', 'mseed-cmd', self._log)
        self._config = config
        # leap seconds not used here, but avoids multiple threads all downloading later
        check_leap(args.leap, args.leap_expire, args.leap_file, args.leap_url, self._log)
        clean_old_files(self._temp_dir, args.temp_expire * 60 * 60 * 24, match_prefixes(RETRIEVEFILE), self._log)

    def do_run(self, args, fetch):
        """
        Set-up environment, parse commands, and delegate to sub-methods as appropriate.
        """
        self._assert_single_use()
        if not exists(self._temp_dir):
            makedirs(self._temp_dir)
        if len(args) == 0 or len(args) > 3:
            raise Exception('Usage: rover %s (file|sncl begin [end])' % RETRIEVE)
        else:
            # input is a temp file as we prepend parameters
            path = unique_path(self._temp_dir, RETRIEVEFILE, args[0])
            try:
                if len(args) == 1:
                    copyfile(args[0], path)
                else:
                    build_file(path, *args)
                self._query(path)
                if fetch:
                    return self._fetch()
                else:
                    return self._display()
            finally:
                safe_unlink(path)

    def _query(self, up):
        """
        Populate the download manager by comparing the data from the
        availability service with the local index.
        """
        if self._pre_index:
            self._log.info('Ensuring index is current before retrieval')
            Indexer(self._config).run([])
        self._prepend_options(up)
        down = self._post_availability(up)
        try:
            self._sort_availability(down)
            for remote in self._parse_availability(down):
                self._log.debug('Available data: %s' % remote)
                local = self._scan_index(remote.sncl)
                self._log.debug('Local data: %s' % local)
                self._request_download(remote.subtract(local))
        finally:
            safe_unlink(down)

    def _fetch(self):
        """
        Fetch data from the download manager.
        """
        result = self._download_manager.download()
        if self._post_compact:
            self._log.info('Checking for duplicate data')
            Compacter(NewConfig(self._config, all=True, compact_list=True, no_index=True)).run([])
        return result

    def _display(self):
        """
        Display data from the download manager.
        """
        return self._download_manager.display()

    def _prepend_options(self, up):
        tmp = unique_path(self._temp_dir, RETRIEVEFILE, up)
        self._log.debug('Prepending options to %s via %s' % (up, tmp))
        try:
            with open(tmp, 'w') as output:
                print('mergequality=true', file=output)
                print('mergesamplerate=true', file=output)
                with open(up, 'r') as input:
                    print(input.readline(), file=output, end='')
            safe_unlink(up)
            copyfile(tmp, up)
        finally:
            safe_unlink(tmp)

    def _post_availability(self, up):
        down = unique_path(self._temp_dir, RETRIEVEFILE, up)
        return post_to_file(self._availability_url, up, down, self._log)

    def _sort_availability(self, down):
        tmp = unique_path(self._temp_dir, RETRIEVEFILE, down)
        try:
            self._log.debug('Sorting %s via %s' % (down, tmp))
            run('sort %s > %s' % (down, tmp), self._log)  # todo - windows
            safe_unlink(down)
            copyfile(tmp, down)
        finally:
            safe_unlink(tmp)

    def _parse_line(self, line):
        n, s, l, c, b, e = line.split()
        return "%s.%s.%s.%s" % (n, s, l, c), parse_epoch(b), parse_epoch(e)

    def _parse_availability(self, down):
        with open(down, 'r') as input:
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
        # todo - we could maybe use time range from initial query?  or from availability?
        availability = SingleSNCLBuilder(self._log, self._timespan_tol, sncl)

        def callback(row):
            availability.add_timespans(row[0], row[1])

        try:
            self.foreachrow('''select timespans, samplerate
                                    from tsindex 
                                    where network=? and station=? and location=? and channel=?
                                    order by starttime, endtime''',
                            sncl.split('.'),
                            callback, quiet=True)
        except OperationalError:
            self._log.debug('No index - first time using rover?')
        return availability.coverage()

    def _request_download(self, missing):
        self._log.debug('Data to download: %s' % missing)
        self._download_manager.add(missing)


def assert_valid_time(time):
    """
    Check timestamp format.
    """
    if match(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?)?$', time):
        return time
    else:
        raise Exception('Invalid time format "%s"' % time)


def build_file(path, sncl, begin, end=None):
    """
    Given a SNCL and begin.end dates, construct an input file in
    the correct (availability service) format.
    """
    parts = list(sncl.split('.'))
    if len(parts) != 4:
        raise Exception('SNCL "%s" does not have 4 components' % sncl)
    parts.append(assert_valid_time(begin))
    if end:
        parts.append(assert_valid_time(end))
    with open(path, 'w') as req:
       print(*parts, file=req)


class Retriever(BaseRetriever):

    __doc__ = BaseRetriever.__doc__

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        return self.do_run(args, True)


class Comparer(BaseRetriever):
    """
### Compare

    rover compare file

    rover compare N.S.L.C begin [end]

Compare available data with the local store, then display what data would be downloaded.  So this command
whows what `rover retrieve` would actually retrieve.

The file argument should contain a list of SNCLs and timespans, as appropriate for calling an Availability
service (eg http://service.iris.edu/irisws/availability/1/).  Otherwise, if a SNCL and timespan are given, a
(single-line) file will be automatically constructed containing that data.

##### Significant Parameters

@availability-url
@timespan-tol
@mseed-db
@verbosity
@log-dir
@log-name
@log-verbosity

##### Examples

    rover compare sncls.txt

will display the data missing form the local store to match what is available for the stations in the given file.

    rover compare IU.ANMO.00.BH1 2017-01-01 2017-01-04

will display the data missing from the local store to match what is available for IU.ANMO.00.BH1.

"""

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        return self.do_run(args, False)
