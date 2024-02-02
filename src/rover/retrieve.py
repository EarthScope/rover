
import datetime
from shutil import copyfile

from rover import __version__
from .args import RETRIEVE, TEMPDIR, AVAILABILITYURL, PREINDEX, UserFeedback, \
    TEMPEXPIRE, LIST_RETRIEVE, DELETEFILES, POSTSUMMARY, DATASELECTURL, fail_early, HTTPTIMEOUT, \
    HTTPRETRIES, OUTPUT_FORMAT, DATADIR, FORCE_METADATA_RELOAD
from .download import DEFAULT_NAME
from .index import Indexer
from .manager import DownloadManager, ManagerException
from .report import Reporter
from .retrieve_metadata import MetadataRetriever
from .sqlite import SqliteSupport
from .summary import Summarizer
from .utils import clean_old_files, match_prefixes, unique_path, \
    safe_unlink, build_file, fix_file_inplace, remove_empty_folders

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

    rover retrieve [net=N] [sta=S] [loc=L] [cha=C] [start [end]]

    rover retrieve N_S_L_C [start [end]]

Compares ROVER's local index with remotely available data, then downloads and
ingest files missing from the local repository. The URL determining the
availability of remote data can be configured by the availability-url option,
and URL controlling data downloads is configured by the dataselect-url
option.

Use ROVER's list-index function to determine data available on a remote server
which is not in the local repository.

##### Significant Options

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
@output-format
@asdf-filename
@force-metadata-reload

In addition, options for sub-commands (download, ingest, index) will be used - see help for those
commands for more details.

##### Examples

    rover retrieve N_S_L_C.txt

processes a file containing a request to download, ingest, and index
data missing from ROVER's local repository.

    rover retrieve IU_ANMO_00_BH1 2017-01-01 2017-01-04

processes a command line request to download, ingest, and index
data missing from ROVER's local repository.

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
        clean_old_files(self._temp_dir, config.arg(TEMPEXPIRE) * 60 * 60 * 24, match_prefixes(RETRIEVEWEB), config.log)

    def do_run(self, args, fetch, command):
        """
        Set-up environment, parse commands, and delegate to sub-methods as appropriate.
        """
        usage = 'Usage: rover %s (file | [net=N] [sta=S] [cha=C] [loc=L] [start [end]] | N_S_L_C [start [end]])' % command
        if not args:
            raise Exception(usage)
        # input is a temp file as we prepend options
        path = unique_path(self._temp_dir, RETRIEVEWEB, args[0])
        try:
            if len(args) == 1:
                copyfile(args[0], path)
            else:
                try:
                    build_file(self._log, path, args)
                except:
                    raise Exception(usage)
            fix_file_inplace(self._log, path, self._temp_dir)
            self._download_manager = DownloadManager(self._config, RETRIEVECONFIG if fetch else None)
            if fetch:
                self._log.default('ROVER version %s - starting retrieve' % __version__)
                self.display_feedback()
            self._query(path, fetch)
            if fetch:
                return self._fetch()
            else:
                return self._display()
        except ManagerException:
            raise
        except Exception as e:
            self._reporter.send_email('ROVER Failure', self._reporter.describe_error(RETRIEVE, e))
            raise
        finally:
            if self._delete_files:
                safe_unlink(path)

    def _query(self, up, fetch):
        """
        Populate the download manager by comparing the data from the
        availability service with the local index.
        """
        if self._pre_index and self._config.arg(OUTPUT_FORMAT).upper() != "ASDF":
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
                self._complete_asdf_retrieve()
        return n_downloads

    def _complete_asdf_retrieve(self):
        if self._config.arg(OUTPUT_FORMAT).upper() == "ASDF":
            # remove empty mseed directories from data directory
            remove_empty_folders(self._config.arg(DATADIR), self._log)
            # load metadata into asdf dataset
            MetadataRetriever(self._config).run([])

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

    rover list-retrieve N_S_L_C [start [end]]

Compares the local index with the requested data remotely available, then
displays the difference. Note that the summary is printed to stdout, while
logging is to stderr.

##### Significant Options

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
