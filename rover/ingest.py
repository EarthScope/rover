
from os import listdir
from os.path import exists, isdir, join, isfile
from re import match
from datetime import datetime

from .index import index, Indexer
from .utils import canonify, run, check_cmd, check_leap, create_parents
from .sqlite import SqliteSupport


# this is the table name when run directly from the command line.
# when run as a worker from (multiple) retriever(s) a table is supplied.
TMPTABLE = 'rover_tmpingest'


class Ingester(SqliteSupport):
    """
    The simplest possible ingester:
    * Uses mseedindx to parse the file.
    * For each section, appends to any existing file using byte offsets
    * Refuses to handle blocks that cross day boundaries
    * Does not check for overlap, differences in sample rate, etc. (see compact)
    """

    def __init__(self, config):
        super().__init__(config)
        args, log = config.args, config.log
        check_cmd('%s -h' % args.mseed_cmd, 'mseedindex', 'mseed-cmd', log)
        self._mseed_cmd = args. mseed_cmd
        self._mseed_db = args.mseed_db
        self._leap_file = check_leap(args.leap, args.leap_expire, args.leap_file, args.leap_url, log)
        self._table = None
        self._mseed_dir = canonify(args.mseed_dir)
        self._log = log
        self._indexer = Indexer(config)

    def ingest(self, args, table=TMPTABLE):
        self._table = table
        for arg in args:
            arg = canonify(arg)
            if not exists(arg):
                raise Exception('Cannot find %s' % arg)
            if isdir(arg):
                self._ingest_dir(arg)
            else:
                self._ingest_file(arg)
        self._indexer.index()

    def _ingest_dir(self, dir):
        for file in listdir(dir):
            path = join(dir, file)
            if isfile(path):
                self._ingest_file(path)
            else:
                self._log.warn('Ignoring %s in %s (not a file)' % (file, dir))

    def _make_destination(self, network, station, starttime):
        date_string = match(r'\d{4}-\d{2}-\d{2}', starttime).group(0)
        time_data = datetime.strptime(date_string, '%Y-%m-%d').timetuple()
        year, day = time_data.tm_year, time_data.tm_yday
        return join(self._mseed_dir, network, str(year), str(day), '%s.%s.%04d.%02d' % (station, network, year, day))

    def _drop_table(self):
        self._execute('drop table if exists %s' % self._table)

    def _ingest_file(self, file):
        self._log.info('Indexing %s for ingest' % file)
        self._drop_table()
        try:
            run('LIBMSEED_LEAPSECOND_FILE=%s %s -sqlite %s -table %s %s'
                % (self._leap_file, self._mseed_cmd, self._mseed_db, self._table, file), self._log)
            rows = self._fetchall('''select network, station, starttime, endtime, byteoffset, bytes 
                                     from %s order by byteoffset''' % self._table)
            self._copy_rows(file, rows)
        finally:
            self._drop_table()

    def _copy_rows(self, file, rows):
        self._log.info('Ingesting %s' % file)
        with open(file, 'rb') as input:
            offset = 0
            for row in rows:
                offset = self._copy_row(offset, input, file, *row)

    def _copy_row(self, offset, input, file, network, station, starttime, endtime, byteoffset, bytes):
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
        return offset

    def _append_data(self, data, dest):
        if not exists(dest):
            create_parents(dest)
            open(dest, 'w').close()
        with open(dest, 'ba') as output:
            output.write(data)

    def _assert_single_day(self, file, starttime, endtime):
        if starttime[:10] != endtime[:10]:
            raise Exception('File %s contains data from more than one day (%s-%s)' % (file, starttime, endtime))


def ingest(config):
    """
    Implement the ingest command.
    """
    Ingester(config).ingest(config.args.args)
