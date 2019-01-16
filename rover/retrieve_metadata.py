import os
import shutil
from collections import namedtuple
from .args import STATIONURL, RETRIEVE_METADATA, UserFeedback, fail_early, \
    HTTPTIMEOUT, HTTPRETRIES, TEMPDIR, OUTPUT_FORMAT, FORCE_METADATA_RELOAD
from .report import Reporter
from .sqlite import SqliteSupport, SqliteContext
from .utils import post_to_file, diagnose_error, unique_path, safe_unlink
from .config import timeseries_db, asdf_container


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO  # python 3


TMPDOWNLOAD = 'rover_metadata_download'


"""
Commands related to metadata retrieval:

The `rover retrieve-metadata` command - check for remote metadata that we
don't already have and download it.
"""

class MetadataRetriever(SqliteSupport, UserFeedback):
    """
### Retrieve

    rover retrieve-metadata

#### Errors, Retries and Consistency

If `download-retries` allows, retrievals are repeated until no errors occur
and, once data appear to be complete, an additional retrieval is made which
should result in no data being downloaded.  If this is not the case - if
additional data are found - then the web services are inconsistent.

Errors and inconsistencies are reported in the logs and in the optional email
(`email` parameter) sent to the user. They also cause the command to exit with
an error status.

##### Examples

If the "output-format" rover.config setting is set to "asdf" then

    rover retrieve-metadata

will download missing metadata from the asdf.h5 repository.
"""

    def __init__(self, config):
        UserFeedback.__init__(self, config)
        SqliteSupport.__init__(self, config)
        fail_early(config)
        self._station_url = config.arg(STATIONURL)
        self._http_timeout = config.arg(HTTPTIMEOUT)
        self._http_retries = config.arg(HTTPRETRIES)
        self._temp_dir = config.dir(TEMPDIR)
        self._reporter = Reporter(config)
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
    
    def process_asdf(self, force_metadata_refresh=False):
        """
        Retrieve metadata and insert into ASDF
        """
        self._log.default("Trying new metadata retrieval.")
        try:
            import pyasdf
            import obspy
        except ImportError:
            raise Exception("Missing required 'pyasdf' python package for "
                            "'output-format=asdf.'") 
        asdf_path = asdf_container(self._config)
        if not os.path.exists(asdf_path):
            raise Exception("No ASDF dataset exists at '{}'. Have you "
                            "run 'rover retrieve'?"
                            .format(asdf_path))
        try:
            ds = pyasdf.ASDFDataSet(asdf_path, mode="a")
            self._log.default("Opened ASDF dataset '{}'"
                              .format(asdf_path))
        except Exception as e:
            raise Exception("Failed to create ASDF file at '{}': {}"
                            .format(asdf_path, e))

        summary_rows = self.fetch_summary_rows()

        # group summary rows by ASDF waveform tag
        grouped_rows = {}
        for row in summary_rows:
            tag = "{}.{}".format(row.network, row.station)
            if not grouped_rows.get(tag):
                grouped_rows[tag] = [row]
            else:
                grouped_rows[tag].append(row)

        # loop over grouped summary rows and compare against ASDF data
        for tag, rows in grouped_rows.items():
            if tag not in ds.waveforms:
                # this should never happen
                self._log.error("Skipping station '{0}'. Found station '{0}' "
                                "in the tsindex_summary table but not in the "
                                "ASDF container.".format(tag))
                continue
            if "StationXML" in ds.waveforms[tag]:
                # read StationXML inventory from ASDF
                asdf_sta_inv = ds.waveforms[tag]["StationXML"]
            else:
                # no StationXML was loaded for tag
                asdf_sta_inv = None
            for row in rows:
                # check if indexed channel exists in ASDF container
                if force_metadata_refresh is True \
                        or asdf_sta_inv is None \
                        or not asdf_sta_inv.select(
                            network=row.network,  station=row.station,
                            location=row.location, channel=row.channel,
                            starttime=row.earliest, endtime=row.latest):
                    self._log.default("Load metadata for "
                                      "'{}.{}.{}.{} | {} - {}' "
                                      "into ASDF."
                                      .format(row.network, row.station,
                                              row.location, row.channel,
                                              row.earliest, row.latest))
                    # download StationXML from fdsnws station service
                    station_xml = self.download_stationxml(row.network,
                                                           row.station,
                                                           row.location,
                                                           row.channel,
                                                           row.earliest,
                                                           row.latest)
                    inv = obspy.read_inventory(station_xml)
                    ds.add_stationxml(inv)
                    safe_unlink(station_xml)
                else:
                    self._log.default("Skip ASDF metadata load for "
                                      "'{}.{}.{}.{} | {} - {}'. "
                                      "Metadata was already loaded."
                                      .format(row.network, row.station,
                                              row.location, row.channel,
                                              row.earliest, row.latest))
        self._log.default("")
        self._log.default("----- Metadata Retrieval Finished -----")
        self._log.default("")
                    

    def run(self, args):
        """
        Set-up environment, parse commands, and delegate to sub-methods as
        appropriate.
        """
        try:
            if self._config.arg(OUTPUT_FORMAT).upper() == "ASDF":
                self.process_asdf(force_metadata_refresh=
                                    self._config.arg(FORCE_METADATA_RELOAD))
            else:
                raise Exception("Incompatible output format. "
                                "Command 'rover retrieve-metadata' "
                                "can only be used with 'output-format=asdf'.")
        except Exception as e:
            self._reporter.send_email('Rover Failure',
                                      self._reporter.describe_error(
                                                        RETRIEVE_METADATA, e))
            raise
            