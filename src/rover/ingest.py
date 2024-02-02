from datetime import datetime
from os import getpid
from os.path import exists, join
from re import match
from shutil import copyfile

from .args import MSEEDINDEXCMD, DATADIR, INDEX, HTTPTIMEOUT, HTTPRETRIES, OUTPUT_FORMAT
from .index import Indexer
from .lock import DatabaseBasedLockFactory, MSEED
from .scan import DirectoryScanner
from .sqlite import SqliteSupport, SqliteContext
from .utils import run, check_cmd, create_parents, safe_unlink, windows, atomic_move, hash

"""
The 'rover ingest' command - copy downloaded data into the repository (and then call index).
"""


# this is the table name when run directly from the command line.
# when run as a worker from (multiple) retriever(s) a table is supplied.
TMPFILE = 'rover_tmp_ingest'


class Ingester(SqliteSupport, DirectoryScanner):
    """
### Ingest

    rover ingest file

Adds contents from a miniSEED formatted file to ROVER's local repository and
indexes the new data.

##### Significant Options

@mseedindex-cmd
@data-dir
@index
@verbosity
@log-dir
@log-verbosity

Options used to configure the sub-command index are also applicable -
see Index help for more details.

##### Examples

    rover ingest /tmp/IU.ANMO.00.*.mseed

will add all the data in the given file to the repository.

"""

# The simplest possible ingester:
# * Uses mseedindex to parse the file.
# * For each section, appends to any existing file using byte offsets
# * Refuses to handle blocks that cross day boundaries
# * Does not check for overlap, differences in sample rate, etc.

    def __init__(self, config):
        SqliteSupport.__init__(self, config)
        DirectoryScanner.__init__(self, config)
        self._mseed_cmd = check_cmd(config, MSEEDINDEXCMD, 'mseedindex')
        self._db_path = None
        self._data_dir = config.dir(DATADIR)
        self._index = config.arg(INDEX)
        self._config = config
        self._log = config.log
        self._lock_factory = DatabaseBasedLockFactory(config, MSEED)

    def run(self, args, db_path=TMPFILE):
        """
        We only support explicit paths - modified file scanning makes no sense because
        the files are external, downloaded data.

        To avoid database contention we can run mseedindex into a unique database path.
        """
        self._db_path = db_path
        if not args:
            raise Exception('No paths provided')
        self.scan_dirs_and_files(args)

    def process(self, temp_file):
        """
        Run mseedindex and, move across the bytes, and then call follow-up tasks.
        """
        self._log.info('Indexing %s for ingest' % temp_file)
        if exists(self._db_path):
            self._log.warn('Temp file %s exists (deleting)' % self._db_path)
            safe_unlink(self._db_path)
        updated = set()
        try:
            run('%s -sqlite %s %s'
                % (self._mseed_cmd, self._db_path, temp_file), self._log)

            with SqliteContext(self._db_path, self._log) as db:
                rows = db.fetchall('''SELECT network, station, starttime, endtime, byteoffset, bytes
                                  FROM tsindex ORDER BY byteoffset''')
                updated.update(self._copy_all_rows(temp_file, rows))
        finally:
            safe_unlink(self._db_path)
        if self._index:
            Indexer(self._config).run(updated)
            if self._config.arg(OUTPUT_FORMAT).upper() == "ASDF":
                from .asdf import ASDFHandler
                # output as ASDF format
                ASDFHandler(self._config).load_miniseed(updated)

    def _copy_all_rows(self, temp_file, rows):
        self._log.info('Ingesting %s' % temp_file)
        updated = set()
        self.updated_files_last_run = []
        with open(temp_file, 'rb') as input_file:
            offset = 0
            for row in rows:
                offset, dest = self._copy_single_row(offset, input_file,
                                                     temp_file, *row)
                updated.add(dest)
        return updated

    def _copy_single_row(self, offset, input_buffer, temp_file, network, station, starttime, endtime, byteoffset, raw_bytes):
        self._assert_single_day(temp_file, starttime, endtime, "%s_%s" % (network, station))
        if offset < byteoffset:
            self._log.warn('Non-contiguous bytes in %s - skipping %d bytes' % (temp_file, byteoffset - offset))
            input_buffer.seek(byteoffset - offset, 1)
            offset = byteoffset
        elif offset > byteoffset:
            raise Exception('Overlapping blocks in %s, index is inconsistent regarding byte ranges)' % temp_file)
        data = input_buffer.read(raw_bytes)
        offset += raw_bytes
        dest = self._make_destination(network, station, starttime)
        self._log.debug('Appending %d bytes from %s at offset %d to %s' % (raw_bytes, temp_file, byteoffset, dest))
        self._append_data(data, dest)
        return offset, dest

    def _make_destination(self, network, station, starttime):
        date_string = match(r'\d{4}-\d{2}-\d{2}', starttime).group(0)
        time_data = datetime.strptime(date_string, '%Y-%m-%d').timetuple()
        year, day = time_data.tm_year, time_data.tm_yday
        return join(self._data_dir, network, str(year), '%03d' % day, '%s.%s.%04d.%03d' % (station, network, year, day))

    def _append_data(self, data, mseed_file):
        # here we are locking for this process, so we can set the PID directly.
        # there is no possibility for deadlock because we are single threaded
        # and release on exit.
        with self._lock_factory.lock(mseed_file, pid=getpid()):
            # to avoid leaving broken files on unexpected exit, use a temp
            # file and then move into position (move should be atomic)
            tmp = mseed_file + '.tmp'
            if exists(tmp):
                self._log.warn('Cleaning %s' % tmp)
                safe_unlink(tmp)
            if not exists(mseed_file):
                create_parents(mseed_file)
                open(tmp, 'w').close()
            else:
                copyfile(mseed_file, tmp)
            with open(tmp, 'ba') as output:
                output.write(data)
            atomic_move(self._log, tmp, mseed_file)

    def _assert_single_day(self, temp_file, starttime, endtime, sid):
        # Comparing time strings, presumed format 'YYYY-MM-DDThh:mm:ss.ssssss'
        if starttime[:10] != endtime[:10]:
            raise Exception('File %s contains data from more than one day (%s-%s) for %s' % (temp_file, starttime, endtime, sid))
