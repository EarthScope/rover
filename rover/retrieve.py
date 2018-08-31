
import datetime
from shutil import copyfile

from .args import RETRIEVE, TEMPDIR, AVAILABILITYURL, PREINDEX, LEAP, LEAPEXPIRE, UserFeedback, \
    LEAPFILE, LEAPURL, TEMPEXPIRE, LIST_RETRIEVE, DELETEFILES, POSTSUMMARY, DATASELECTURL, fail_early, HTTPTIMEOUT, \
    HTTPRETRIES, ROVER_VERSION
from .download import DEFAULT_NAME
from .index import Indexer
from .manager import DownloadManager, ManagerException
from .report import Reporter
from .sqlite import SqliteSupport
from .summary import Summarizer
from .utils import clean_old_files, match_prefixes, check_leap, unique_path, safe_unlink, build_file

"""
Commands related to data retrieval:

The `rover retrieve` command - check for remote data that we don't already have, download it and ingest it.
The `rover list-retrieve` command - shows what data would be downloaded by `rover retrieve`.
"""


RETRIEVEWEB = 'rover_retrieve_availability'
RETRIEVECONFIG = 'rover_retrieve_config'
EARLY = datetime.datetime(1900, 1, 1)


class BaseRetriever(SqliteSupport, UserFeedback):
    """
### Retrieve

    rover retrieve file

    rover retrieve [net=N] [sta=S] [loc=L] [cha=C] [begin [end]]

    rover retrieve N_S_L_C [begin [end]]

Compare available data with the repository, then download, ingest and index data.

The file argument should contain a list of Net_Sta_Loc_Chans and timespans, as appropriate for calling an Availability
service (eg http://service.iris.edu/irisws/availability/1/).

In the second form above, at least one of `net`, `sta`, `loc`, `cha` should be given (missing values are
taken as wildcards).  For this and the third form a (single-line) file will be automatically constructed
containing that data.

The list of available data is retrieved from the service and compared with the local index.  Data not
available locally are downloaded and ingested.

In the comparison of available data, maximal timespans across all quality and sample rates are used (so quality
and samplerate information is "merged").

This command also indexes modified data in the repository before processing.

When the process is running status should be visible at http://localhost:8000 (by default).  When the process
ends an email can be sent to the user (if `--email` is used).

See `rover subscribe` for similar functionality, but with regular updates.

#### Errors, Retries and Consistency

If `download-retries` allows, retrievals are repeated until no errors occur and, once data appear to be complete,
an additional retrieval is made which should result in no data being downloaded.  If this is not the case - if
additional data are found - then the web services are inconsistent.

Errors and inconsistencies are reported in the logs and in the optional email (`email` parameter) sent to the user.
They also cause the command to exit with an error status.

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
@mseedindex-cmd
@data-dir
@download-workers
@download-retries
@http-timeout
@http-retries
@leap-expire
@leap-file
@leap-url
@web
@http-bind-address
@http-port
@email
@email-from
@smtp-address
@smtp-port
@verbosity
@log-dir
@log-verbosity
@temp-expire

In addition, parameters for sub-commands (download, ingest, index) will be used - see help for those
commands for more details.

##### Examples

    rover retrieve N_S_L_C.txt

will download, ingest, and index any data missing from the repository for N_S_L_Cs / timespans present in the given file.

    rover retrieve IU_ANMO_00_BH1 2017-01-01 2017-01-04

will download, ingest and index and data for IU_ANMO_00_BH1 between the given dates that are missing from the repository.

"""

    def __init__(self, config):
        UserFeedback.__init__(self, config)
        SqliteSupport.__init__(self, config)
        fail_early(config)
        self._temp_dir = config.dir(TEMPDIR)
        self._availability_url = config.arg(AVAILABILITYURL)
        self._dataselect_url = config.arg(DATASELECTURL)
        self._pre_index = config.arg(PREINDEX)
        self._delete_files = config.arg(DELETEFILES)
        self._post_summary = config.arg(POSTSUMMARY)
        self._download_manager = None   # created in do_run()
        self._reporter = Reporter(config)
        self._config = config
        # leap seconds not used here, but avoids multiple threads all downloading later
        check_leap(config.arg(LEAP), config.arg(LEAPEXPIRE), config.file(LEAPFILE), config.arg(LEAPURL),
                   config.arg(HTTPTIMEOUT), config.arg(HTTPRETRIES), config.log)
        clean_old_files(self._temp_dir, config.arg(TEMPEXPIRE) * 60 * 60 * 24, match_prefixes(RETRIEVEWEB), config.log)

    def do_run(self, args, fetch, command):
        """
        Set-up environment, parse commands, and delegate to sub-methods as appropriate.
        """
        usage = 'Usage: rover %s (file | [net=N] [sta=S] [cha=C] [loc=L] [begin [end]] | N_S_L_C [begin [end]])' % command
        if not args:
            raise Exception(usage)
        # input is a temp file as we prepend parameters
        path = unique_path(self._temp_dir, RETRIEVEWEB, args[0])
        try:
            if len(args) == 1:
                copyfile(args[0], path)
            else:
                try:
                    build_file(self._log, path, args)
                except:
                    raise Exception(usage)
            self._download_manager = DownloadManager(self._config, RETRIEVECONFIG if fetch else None)
            if fetch:
                self._log.default('Rover version %s - starting retrieve' % ROVER_VERSION)
                self.display_feedback()
            self._query(path, fetch)
            if fetch:
                return self._fetch()
            else:
                return self._display()
        except ManagerException:
            raise
        except Exception as e:
            self._reporter.send_email('Rover Failure', self._reporter.describe_error(RETRIEVE, e))
            raise
        finally:
            if self._delete_files:
                safe_unlink(path)

    def _query(self, up, fetch):
        """
        Populate the download manager by comparing the data from the
        availability service with the local index.
        """
        if self._pre_index:
            self._log.info('Ensuring index is current before retrieval')
            Indexer(self._config).run([])
        self._download_manager.add(DEFAULT_NAME, up, fetch,
                                   self._availability_url, self._dataselect_url, self._source_callback)

    def _fetch(self):
        """
        Fetch data from the download manager.
        """
        try:
            n_downloads = self._download_manager.download()
        finally:
            if self._post_summary:
                Summarizer(self._config).run([])
        return n_downloads

    def _display(self):
        """
        Display data from the download manager.
        """
        return self._download_manager.display()

    def _source_callback(self, source):
        subject, msg = self._reporter.describe_retrieve(source)
        self._reporter.send_email(subject, msg)


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

    rover list-retrieve N_S_L_C [begin [end]]

Display what data would be downloaded if the `retrieve` equivalent command was run.

The file argument should contain a list of Net_Sta_Loc_Chans and timespans, as appropriate for calling an Availability
service (eg http://service.iris.edu/irisws/availability/1/).  Otherwise, if a N_S_L_C and timespan are given, a
(single-line) file will be automatically constructed containing that data.

##### Significant Parameters

@availability-url
@timespan-tol
@data-dir
@verbosity
@log-dir
@log-verbosity

##### Examples

    rover list-retrieve N_S_L_C.txt

will display the data missing form the repository to match what is available for the stations in the given file.

    rover list-retrieve IU.ANMO.00.BH1 2017-01-01 2017-01-04

will display the data missing from the repository to match what is available for IU.ANMO.00.BH1.

"""

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        return self.do_run(args, False, LIST_RETRIEVE)
