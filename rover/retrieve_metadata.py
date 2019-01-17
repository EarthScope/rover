import os
import shutil
from collections import namedtuple
from .args import STATIONURL, RETRIEVE_METADATA, UserFeedback, fail_early, \
    HTTPTIMEOUT, HTTPRETRIES, TEMPDIR, OUTPUT_FORMAT
from .report import Reporter
from .sqlite import SqliteSupport, SqliteContext, NoResult
from .summary import Summarizer
from .utils import post_to_file, diagnose_error, unique_path, safe_unlink
from .config import timeseries_db


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO  # python 3


TMPDOWNLOAD = 'rover_metadata_download'


class MetadataSource(SqliteSupport, UserFeedback):
    
    def __init__(self, config):
        UserFeedback.__init__(self, config)
        SqliteSupport.__init__(self, config)
        self._station_url = config.arg(STATIONURL)
        self._http_timeout = config.arg(HTTPTIMEOUT)
        self._http_retries = config.arg(HTTPRETRIES)
        self._temp_dir = config.dir(TEMPDIR)
        self._config = config
        
    def _do_download(self, url, in_path, out_path):
        try:
            response, check_status = post_to_file(url, in_path, out_path,
                                                  self._http_timeout,
                                                  self._http_retries,
                                                  self._log)
            check_status()
        except Exception as e:
            diagnose_error(self._log, str(e), in_path,
                           out_path, copied=False)
            raise
        return response
    
    def download_stationxml(self, net_code, sta_code, loc_code, cha_code,
                            starttime, endtime):
        '''
        Create station web service post request for fdsnws-station service
        and return StationXML.
        '''
        request_path = unique_path(self._temp_dir,
                                  TMPDOWNLOAD,
                                  str(os.getpid()))
        stationxml_path = unique_path(self._temp_dir,
                                       TMPDOWNLOAD,
                                       str(os.getpid()))
        ws_request = StringIO()
        ws_request.write("level=response\n"
                         "includecomments=false\n")
        ws_request.write("{} {} {} {} {} {}\n".format(net_code, sta_code,
                                                      loc_code, cha_code,
                                                      starttime, endtime))
        with open(request_path, 'w') as fd:
            ws_request.seek(0)
            shutil.copyfileobj(ws_request, fd)
        stationxml = self._do_download(self._station_url,
                                       request_path,
                                       stationxml_path)
        safe_unlink(request_path)
        return stationxml
    
    def has_tsindex(self):
        with SqliteContext(timeseries_db(self._config), self._log) as db:
            try:
                db.fetchone(
                    "SELECT name "
                    "FROM sqlite_master "
                    "WHERE type='table' AND name='tsindex'")
                return True
            except NoResult:
                return False

    def has_tsindex_summary(self):
        with SqliteContext(timeseries_db(self._config), self._log) as db:
            try:
                db.fetchone(
                    "SELECT name "
                    "FROM sqlite_master "
                    "WHERE type='table' AND name='tsindex_summary'")
                return True
            except NoResult:
                return False
    
    def fetch_summary_rows(self):
        '''
        Fetch all summary rows.

        Returns rows as list of named tuples containing:
        (network,station,location,channel,earliest,latest,updated)

        :rtype: list(tuple)
        :returns: Return rows as list of named tuples containing:
            (network, station, location, channel, earliest, latest, updated).
        '''
        NamedRow = namedtuple('NamedRow',
                              ['network', 'station', 'location', 'channel',
                               'earliest', 'latest', 'updated'])
        named_summary_rows = []
        try:
            with SqliteContext(timeseries_db(self._config), self._log) as db:
                if not self.has_tsindex():
                    raise Exception("No index - first time using rover?"
                                    .format(timeseries_db(self._config)))
                elif not self.has_tsindex_summary():
                    raise Exception("No index summary exists in database "
                                    "'{}'. Run `rover summary` to create one."
                                    .format(timeseries_db(self._config)))
                summary_rows = db.fetchall(
                        "SELECT DISTINCT s.network,s.station,s.location,"
                        "s.channel,s.earliest,s.latest,s.updt "
                        "FROM tsindex_summary s "
                        "ORDER BY s.network, s.station, s.location, "
                        "s.channel, s.earliest, s.latest")
                for row in summary_rows:
                    named_summary_rows.append(NamedRow(*row))
        except Exception as err:
            raise ValueError(str(err))

        self._log.default("Fetched %d summary rows from "
                          "tsindex_summary table." % len(named_summary_rows))
        return named_summary_rows

"""
Commands related to metadata retrieval:

The `rover retrieve-metadata` command - check for remote metadata that we
don't already have and download it.
"""

class MetadataRetriever(UserFeedback):
    """
### Retrieve

    rover retrieve-metadata

Download missing metadata from the fdsnws-station web service and save to the
data archive. This feature is currently supported only for the ASDF output
format.

#### Errors, Retries and Consistency

If `download-retries` allows, retrievals are repeated until no errors occur
and, once data appear to be complete, an additional retrieval is made which
should result in no data being downloaded.  If this is not the case - if
additional data are found - then the web services are inconsistent.

If `force-metadata-reload` is True then already loaded metadata will be
downloaded and overwritten.

Errors and inconsistencies are reported in the logs and in the optional email
(`email` parameter) sent to the user. They also cause the command to exit with
an error status.

##### Significant Parameters

@temp-dir
@station-url
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

##### Examples

If the "output-format" rover.config setting is set to "asdf" then

    rover retrieve-metadata

will download missing metadata from the asdf.h5 repository.
"""

    def __init__(self, config):
        UserFeedback.__init__(self, config)
        fail_early(config)
        self._reporter = Reporter(config)
        self._config = config
    
    def process_asdf(self):
        """
        Retrieve metadata and insert into ASDF
        """
        from .asdf import ASDFHandler
        source = MetadataSource(self._config)
        ASDFHandler(self._config).load_metadata(source)

    def run(self, arg):
        """
        Set-up environment, parse commands, and delegate to sub-methods as
        appropriate.
        """
        try:
            self._log.default("Trying new metadata retrieval.")
            
            if not os.path.exists(timeseries_db(self._config)):
                raise Exception("No timeseries index database exists at {}."
                                .format(timeseries_db(self._config)))
            
            if self._config.arg(OUTPUT_FORMAT).upper() == "ASDF":
                self.process_asdf()
            else:
                raise Exception("Incompatible output format. "
                                "Command 'rover retrieve-metadata' "
                                "can only be used with 'output-format=asdf'.")
            self._log.default("")
            self._log.default("----- Metadata Retrieval Finished -----")
            self._log.default("")
        except Exception as e:
            self._reporter.send_email('Rover Failure',
                                      self._reporter.describe_error(
                                                        RETRIEVE_METADATA, e))
            raise
            