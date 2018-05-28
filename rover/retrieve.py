
import datetime
from os import makedirs
from os.path import exists
from shutil import copyfile
from sqlite3 import OperationalError

from .args import RETRIEVE, TEMPDIR, AVAILABILITYURL, TIMESPANTOL, PREINDEX, ROVERCMD, MSEEDCMD, LEAP, LEAPEXPIRE, \
    LEAPFILE, LEAPURL, TEMPEXPIRE, LIST_RETRIEVE, DELETEFILES, POSTSUMMARY, DATASELECTURL
from .coverage import SingleSNCLBuilder, Coverage
from .download import DownloadManager
from .index import Indexer
from .sqlite import SqliteSupport
from .summary import Summarizer
from .utils import post_to_file, run, check_cmd, clean_old_files, \
    match_prefixes, check_leap, parse_epoch, unique_path, safe_unlink, build_file


"""
Commands related to data retrieval:
 
The `rover retrieve` command - check for remote data that we don't already have, download it and ingest it.
The `rover list-retrieve` command - shows what data would be downloaded by `rover retrieve`.
"""


RETRIEVEWEB = 'rover_retrieve_web'
RETRIEVECONFIG = 'rover_retrieve_config'
EARLY = datetime.datetime(1900, 1, 1)
DEFAULT = 'default'


class BaseRetriever(SqliteSupport):
    """
### Retrieve

    rover retrieve file

    rover retrieve [net=N] [sta=S] [loc=L] [cha=C] begin [end]

    rover retrieve N_S_L_C begin [end]

Compare available data with the local store, then download, ingest and index data.

The file argument should contain a list of SNCLs and timespans, as appropriate for calling an Availability
service (eg http://service.iris.edu/irisws/availability/1/).

In the second form above, at least one of `net`, `sta`, `loc`, `cha` should be given (missing values are
taken as wildcards).  For this and the third form a (single-line) file will be automatically constructed
containing that data.

The list of available data is retrieved from the service and compared with the local index.  Data not
available locally are downloaded and ingested.

In the comparison of available data, maximal timespans across all quality and sample rates are used (so quality
and samplerate information is "merged").

This command also indexes modified data in the store before processing.

##### Significant Parameters

@temp-dir
@availability-url
@dataselect-url
@timespan-tol
@pre-index
@ingest
@index
@post-summary
@rover-cmd
@mseed-cmd
@mseed-db
@download-workers
@verbosity
@log-dir
@log-name
@log-verbosity

In addition, parameters for sub-commands (download, ingest, index) will be used - see help for those
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
        self._download_manager = DownloadManager(config, RETRIEVECONFIG)
        self._temp_dir = config.dir_path(TEMPDIR)
        self._availability_url = config.arg(AVAILABILITYURL)
        self._dataselect_url = config.arg(DATASELECTURL)
        self._timespan_tol = config.arg(TIMESPANTOL)
        self._pre_index = config.arg(PREINDEX)
        self._delete_files = config.arg(DELETEFILES)
        self._post_summary = config.arg(POSTSUMMARY)
        # check these so we fail early
        check_cmd(config.arg(ROVERCMD), 'rover', 'rover-cmd', config.log)
        check_cmd(config.arg(MSEEDCMD), 'mseedindex', 'mseed-cmd', config.log)
        self._config = config
        # leap seconds not used here, but avoids multiple threads all downloading later
        check_leap(config.arg(LEAP), config.arg(LEAPEXPIRE), config.arg(LEAPFILE), config.arg(LEAPURL), config.log)
        clean_old_files(self._temp_dir, config.arg(TEMPEXPIRE) * 60 * 60 * 24, match_prefixes(RETRIEVEWEB), config.log)

    def do_run(self, args, fetch, command):
        """
        Set-up environment, parse commands, and delegate to sub-methods as appropriate.
        """
        if not exists(self._temp_dir):
            makedirs(self._temp_dir)
        # input is a temp file as we prepend parameters
        path = unique_path(self._temp_dir, RETRIEVEWEB, args[0])
        try:
            if len(args) == 1:
                copyfile(args[0], path)
            else:
                try:
                    build_file(path, args)
                except:
                    raise Exception('Usage: rover %s (file | [net=N] [sta=S] [cha=C] [loc=L] begin [end] | sncl begin [end])' % command)
            self._query(path)
            if fetch:
                return self._fetch()
            else:
                return self._display()
        finally:
            if self._delete_files:
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
        self._download_manager.add_source(DEFAULT, self._dataselect_url)
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
        n_downloads = self._download_manager.download()
        if self._post_summary:
            Summarizer(self._config).run([])
        return n_downloads

    def _display(self):
        """
        Display data from the download manager.
        """
        return self._download_manager.display()

    def _prepend_options(self, up):
        tmp = unique_path(self._temp_dir, RETRIEVEWEB, up)
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
        down = unique_path(self._temp_dir, RETRIEVEWEB, up)
        return post_to_file(self._availability_url, up, down, self._log)

    def _sort_availability(self, down):
        tmp = unique_path(self._temp_dir, RETRIEVEWEB, down)
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
        self._download_manager.add_coverage(DEFAULT, missing)


class Retriever(BaseRetriever):

    __doc__ = BaseRetriever.__doc__

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        return self.do_run(args, True, RETRIEVE)


class ListRetriever(BaseRetriever):
    """
### List Retrieve

    rover list-retrieve file

    rover list-retrieve N_S_L_C begin [end]

Display what data would be downloaded if the `retrieve` equivalent command was run.

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

    rover list-retrieve sncls.txt

will display the data missing form the local store to match what is available for the stations in the given file.

    rover list-retrieve IU.ANMO.00.BH1 2017-01-01 2017-01-04

will display the data missing from the local store to match what is available for IU.ANMO.00.BH1.

"""

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        return self.do_run(args, False, LIST_RETRIEVE)
