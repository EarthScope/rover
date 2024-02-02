import os
from .args import FORCE_METADATA_RELOAD, UserFeedback, \
    fail_early
from .config import asdf_container, timeseries_db
from .utils import safe_unlink
from .sqlite import SqliteContext
from .lock import DatabaseBasedLockFactory, ASDF

try:
    import pyasdf
    import obspy
except ImportError:
    raise Exception("Missing required 'pyasdf' python package for "
                    "'output-format=asdf.'") 

class ASDFHandler(UserFeedback):
    
    def __init__(self, config):
        UserFeedback.__init__(self, config)
        fail_early(config)
        self.asdf_path = asdf_container(config)
        self._config = config
        self._lock_factory = DatabaseBasedLockFactory(config, ASDF)
        
    def _get_asdf_dataset(self):
            try:
                ds = pyasdf.ASDFDataSet(self.asdf_path, mode="a")
                self._log.debug("Opened ASDF dataset '{}'."
                                .format(self.asdf_path))
            except Exception as e:
                raise Exception("Failed to create ASDF file at '{}': {}."
                                .format(self.asdf_path, e))
            return ds
        
    def load_miniseed(self, mseed_file_list):
        """
        Load miniSEED data into the ASDF archive and remove miniSEED file.
        """
        lock = self._lock_factory.lock(self.asdf_path, pid=os.getpid())
        lock.acquire()
        with SqliteContext(
                timeseries_db(self._config), self._log) as db:
            for mseed_file in mseed_file_list:
                # a context manager is used to ensure that the ASDF dataset
                # object is deleted so that other processes can use the file 
                with self._get_asdf_dataset() as ds:
                    st = obspy.read(mseed_file)
                    for trace in st:
                        # write timeseries to asdf file
                        self._log.default("Add '{}' to ASDF."
                                          .format(trace))
                        ds.append_waveforms(trace,
                                            tag="raw_recording")
                        # update miniSEED TSIndex records
                        # (format= “ASDF”, filename=<ASDF_FILENAME>)
                        db.execute("UPDATE tsindex "
                                   "SET filename='{0}', format='ASDF', "
                                   "byteoffset=null, hash=null "
                                   "WHERE filename='{1}'"
                                   .format(self.asdf_path, mseed_file))
                    # remove miniseed that was inserted into ASDF
                    safe_unlink(mseed_file)
        lock.release()
        
        
    def load_metadata(self, source):
        lock = self._lock_factory.lock(self.asdf_path, pid=os.getpid())
        lock.acquire()
        summary_rows = source.fetch_summary_rows()
        # group summary rows by ASDF waveform tag
        grouped_rows = {}
        for row in summary_rows:
            tag = "{}.{}".format(row.network, row.station)
            if not grouped_rows.get(tag):
                grouped_rows[tag] = [row]
            else:
                grouped_rows[tag].append(row)
    
        with self._get_asdf_dataset() as ds:
            # loop over grouped summary rows and compare against ASDF data
            for tag, rows in grouped_rows.items():
                if tag not in ds.waveforms:
                    # this should never happen
                    self._log.error("Skipping station '{0}'. Found station "
                                    "'{0}' in the tsindex_summary table but "
                                    "not in the ASDF container.".format(tag))
                    continue
                if "StationXML" in ds.waveforms[tag]:
                    # read StationXML inventory from ASDF
                    asdf_sta_inv = ds.waveforms[tag]["StationXML"]
                else:
                    # no StationXML was loaded for tag
                    asdf_sta_inv = None
                for row in rows:
                    # check if indexed channel exists in ASDF container
                    if self._config.arg(FORCE_METADATA_RELOAD) is True \
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
                        station_xml = source.download_stationxml(row.network,
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
        lock.release()
