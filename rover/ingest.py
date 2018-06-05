
from datetime import datetime
from os.path import exists, join
from re import match

from .args import MSEEDINDEXCMD, LEAP, LEAPEXPIRE, LEAPFILE, LEAPURL, MSEEDDIR, INDEX, HTTPTIMEOUT, HTTPRETRIES
from .index import Indexer
from .lock import DatabaseBasedLockFactory, MSEED
from .scan import DirectoryScanner
from .sqlite import SqliteSupport, SqliteContext
from .utils import run, check_cmd, check_leap, create_parents, touch, safe_unlink

"""
The 'rover ingest' command - copy downloaded data into the local store (and then call index).
"""


# this is the table name when run directly from the command line.
# when run as a worker from (multiple) retriever(s) a table is supplied.
TMPFILE = 'rover_tmp_ingest'


class Ingester(SqliteSupport, DirectoryScanner):
    """
### Ingest

    rover ingest file

Add the contents of the file (MSEED format) to the local store and index the new data.

The `mseedindex` command is used to index the different blocks of dta present in the file.  THe corresponding byte
ranges are then appended to the appropriate files in the local store.

The file should not contain data that spans multiple calendar days.

##### Significant Parameters

@mseedindex-cmd
@mseed-dir
@index
@leap
@leap-expire
@leap-file
@leap-url
@verbosity
@log-dir
@log-verbosity

In addition, parameters for sub-commands (index) will be used - see help for those commands
for more details.

##### Examples

    rover ingest /tmp/IU.ANMO.00.*.mseed

will add all the data in the given file to the local store.

"""

# The simplest possible ingester:
# * Uses mseedindx to parse the file.
# * For each section, appends to any existing file using byte offsets
# * Refuses to handle blocks that cross day boundaries
# * Does not check for overlap, differences in sample rate, etc.

    def __init__(self, config):
        SqliteSupport.__init__(self, config)
        DirectoryScanner.__init__(self, config)
        self._mseed_cmd = check_cmd(config, MSEEDINDEXCMD, 'mseedindex')
        self._leap_file = check_leap(config.arg(LEAP), config.arg(LEAPEXPIRE), config.arg(LEAPFILE),
                                     config.arg(LEAPURL), config.arg(HTTPTIMEOUT), config.arg(HTTPRETRIES), config.log)
        self._db_path = None
        self._mseed_dir = config.dir_path(MSEEDDIR)
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

    def process(self, file):
        """
        Run mseedindex and, move across the bytes, and then call follow-up tasks.
        """
        self._log.info('Indexing %s for ingest' % file)
        if exists(self._db_path):
            self._log.warn('Temp file %s exists (deleting)' % self._db_path)
            safe_unlink(self._db_path)
        updated = set()
        try:
            run('LIBMSEED_LEAPSECOND_FILE=%s %s -sqlite %s %s'
                % (self._leap_file, self._mseed_cmd, self._db_path, file), self._log)
            with SqliteContext(self._db_path, self._log) as db:
                rows = db.fetchall('''select network, station, starttime, endtime, byteoffset, bytes
                                  from tsindex order by byteoffset''')
                updated.update(self._copy_all_rows(file, rows))
        finally:
            safe_unlink(self._db_path)
        if self._index:
            Indexer(self._config).run(updated)

    def _copy_all_rows(self, file, rows):
        self._log.info('Ingesting %s' % file)
        updated = set()
        with open(file, 'rb') as input:
            offset = 0
            for row in rows:
                offset, dest = self._copy_single_row(offset, input, file, *row)
                updated.add(dest)
        return updated

    def _copy_single_row(self, offset, input, file, network, station, starttime, endtime, byteoffset, bytes):
        self._assert_single_day(file, starttime, endtime)
        if offset < byteoffset:
            self._log.warn('Non-contiguous bytes in %s - skipping %d bytes' % (file, byteoffset - offset))
            input.read(byteoffset - offset)
            offset = byteoffset
        elif offset > byteoffset:
            raise Exception('Overlapping blocks in %s (mseedindex bug?)' % file)
        data = input.read(bytes)
        offset += bytes
        dest = self._make_destination(network, station, starttime)
        self._log.debug('Appending %d bytes from %s at offset %d to %s' % (bytes, file, byteoffset, dest))
        self._append_data(data, dest)
        return offset, dest

    def _make_destination(self, network, station, starttime):
        date_string = match(r'\d{4}-\d{2}-\d{2}', starttime).group(0)
        time_data = datetime.strptime(date_string, '%Y-%m-%d').timetuple()
        year, day = time_data.tm_year, time_data.tm_yday
        return join(self._mseed_dir, network, str(year), '%03d' % day, '%s.%s.%04d.%03d' % (station, network, year, day))

    def _append_data(self, data, dest):
        if not exists(dest):
            create_parents(dest)
            open(dest, 'w').close()
        with self._lock_factory.lock(dest):
            with open(dest, 'ba') as output:
                output.write(data)

    def _assert_single_day(self, file, starttime, endtime):
        if starttime[:10] != endtime[:10]:
            raise Exception('File %s contains data from more than one day (%s-%s)' % (file, starttime, endtime))
