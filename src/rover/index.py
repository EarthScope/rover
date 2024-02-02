
import sys
from re import match, sub
from sqlite3 import OperationalError

from .config import timeseries_db
from .args import MSEEDINDEXCMD, DEV, VERBOSITY, MSEEDINDEXWORKERS, HTTPTIMEOUT, HTTPRETRIES, FORCECMD, TIMESPANINC
from .args import TIMESPANTOL
from .coverage import MultipleSNCLBuilder
from .help import HelpFormatter
from .scan import ModifiedScanner, DirectoryScanner
from .sqlite import SqliteSupport
from .utils import format_epoch, windows, tidy_timestamp
from .utils import check_cmd, STATION, NETWORK, CHANNEL, LOCATION
from .workers import Workers


"""
Commands related to the index:

The 'rover index' command - call mseeedindex to update the tsindex table.
The 'rover list-index' command - displays entries from the tsindex table.
"""


class Indexer(ModifiedScanner, DirectoryScanner):
    """
### Index

    rover index [--all]

    rover index (file|dir)+

Indexes files, adds or changes entries in the tsindex table stored in the
miniSEED database.

When no argument is given, all modified files in the repository are processed.
The `--all` flag forces all files to be processed. If a path argument
is provided, all files contained in the directory are processed, along with
the contents of sub-directories, unless `--no-recurse` is specified.

##### Significant Options

@all
@data-dir
@mseedindex-cmd
@mseedindex-workers
@verbosity
@log-dir
@log-verbosity

##### Examples

    rover index --all

will index the entire repository.

"""

# Most of the work is done in the scanner superclasses which find the files
# to modify, and in the worker that runs mseedindex.

    def __init__(self, config):
        ModifiedScanner.__init__(self, config)
        DirectoryScanner.__init__(self, config)
        self._mseed_cmd = check_cmd(config, MSEEDINDEXCMD, 'mseedindex')
        self._timeseries_db = timeseries_db(config)
        self._verbose = config.arg(DEV) and config.arg(VERBOSITY) == 5
        self._workers = Workers(config, config.arg(MSEEDINDEXWORKERS))

    def run(self, args):
        """
        Find the files to process (see superclasses).
        """
        if not args:
            self._log.info('Indexing all changed files')
            self.scan_data_dir()
        else:
            self.scan_dirs_and_files(args)

    def process(self, path):
        """
        Run mseedindex asynchronously in a worker.
        """
        self._log.info('Indexing %s' % path)
        self._workers.execute('%s %s -sqlite %s %s'
                              % (self._mseed_cmd, '-v -v' if self._verbose else '',
                                 self._timeseries_db, path))

    def done(self):
        self._workers.wait_for_all()


START = 'start'
END = 'end'
COUNT = 'count'
JOIN = 'join'
JOIN_QSR = 'join-qsr'
QUALITY = 'quality'
SAMPLERATE = 'samplerate'


class IndexLister(SqliteSupport, HelpFormatter):
    """
### List Index

    rover list-index [net=...|sta=...|loc=...|cha=..|qua=...|samp=...]* [start=...] [end=...] \\
    [count|join|join-qsr]

    rover list-index [N_S_L_C_Q]* [start=...] [end=...] \\
    [count|join|join-qsr]

List an index of entries for a ROVER repository, defined by the the data-dir
configuration options, that match given constraints. For more information,
run "rover list-index" with no arguments.

Flag options used to change the output format are optional arguments.
Flags are mutually exclusive and take no value:

  count - only the number of matches will be shown

  join - continguous time ranges will be joined

  join-qsr - the maximal timespan across all quality and samplerates is shown
  (as used by retrieve)

##### Significant Options

@timespan-tol
@data-dir
@verbosity
@log-dir
@log-verbosity

#### Examples

    rover list-index IU_ANMO_00_BH? count

will display the number of entries for all time, and any quality or smaplerate.

    rover list-index net=* start=2001-01-01

will list all entries in the index after the year 2000.

"""

    def __init__(self, config):
        SqliteSupport.__init__(self, config)
        HelpFormatter.__init__(self, False)
        self._timespan_inc = config.arg(TIMESPANINC)
        self._timespan_tol = config.arg(TIMESPANTOL)
        self._timeseries_db = timeseries_db(config)
        self._multiple_constraints = {STATION: [],
                                      NETWORK: [],
                                      CHANNEL: [],
                                      LOCATION: [],
                                      QUALITY: [],
                                      SAMPLERATE: []}
        self._single_constraints = {START: None,
                                    END: None}
        self._flags = {COUNT: False, JOIN: False, JOIN_QSR: False}

    def _display_help(self):
        self.print_help('''
The list-index command prints entries from the index that match
the query parameters.  Parameters generally have the form
name=value (no spaces).

The following parameters take '*' and '?' as wildcards, can be
repeated for multiple matches (combined with 'OR"), and the name
only has to match unambiguously (so cha=HHZ is OK):

  station, network, channel, location, quality, samplerate

The short form N_S_L_C_Q can also be used.

The following parameters can be given only once, must be of
the form YYYY-MM-DDTHH:MM:SS.SSSSSS (may be truncated on the
right), and define a range of times over which the block must
appear (at least partially) to be included:

  start, end

The following parameters are simple flags that change the
output format.  They are mutually exclusive and take no
value:

  count - only the number of matches will be shown

  join - contiguous time ranges will be joined

  join-qsr - the maximal timespan across all quality and
  samplerates is shown (as used by retrieve)

Examples:

    rover list-index IU_ANMO_00_BH? count

will display the number of entries for all time, any
quality or smaplerate.

    rover list-index net=* start=2001-01-01

will list all entries in the index after the year 2000.

Note that console logging is to stderr, while results are
printed to stdout.

''')

    def run(self, args, stdout=None):
        if not stdout: stdout = sys.stdout
        if not args:
            self._display_help()
        else:
            self._check_database()
            self._parse_args(args)
            sql, params = self._build_query()
            if self._flags[COUNT]:
                self._count(sql, params, stdout=stdout)
            else:
                self._rows(sql, params, stdout=stdout)

    def _check_database(self):
        try:
            self.execute('SELECT count(*) FROM tsindex')
        except OperationalError:
            raise Exception('''Cannot access the index table in the database (%s).  Bad configuration or no data indexed?''' % self._timeseries_db)

    def _parse_args(self, args):
        for arg in args:
            if arg in self._flags:
                self._assert_unset_flags(arg)
                self._flags[arg] = True
            else:
                parts = arg.split('=')
                if len(parts) == 1:
                    self._set_snclq(arg)
                elif len(parts) != 2:
                    raise Exception('Cannot parse "%s" (not of form name=value)' % arg)
                else:
                    name, value = parts
                    if name in (START, END):
                        self._set_time_limit(name, value)
                    else:
                        self._set_name_value(name, value)
        if self._flags[JOIN_QSR] and (
                self._multiple_constraints[SAMPLERATE] or self._multiple_constraints[QUALITY]):
            raise Exception('Cannot specify %s / %s AND %s' % (QUALITY, SAMPLERATE, JOIN_QSR))

    def _assert_unset_flags(self, name1):
        for name2 in self._flags:
            if self._flags[name2]:
                raise Exception('Cannot specify multiple keys (%s, %s)' % (name1, name2))

    def _set_snclq(self, snclq):
        components = snclq.split('_')
        if len(components) < 2 or len(components) > 5:
            raise Exception('Cannot parse %s (expect 2 to 5 values separated by "_" for N_S_L_C_Q)' % snclq)
        self._set_name_value(NETWORK, components[0])
        self._set_name_value(STATION, components[1])
        if len(components) > 2: self._set_name_value(LOCATION, components[2])
        if len(components) > 3: self._set_name_value(CHANNEL, components[3])
        if len(components) > 4: self._set_name_value(QUALITY, components[4])

    def _set_time_limit(self, name, value):
        if self._single_constraints[name]:
            raise Exception('Multiple values for %s' % name)
        value = tidy_timestamp(self._log, value)
        self._single_constraints[name] = value
        if self._single_constraints[START] and self._single_constraints[END] \
                and self._single_constraints[START] > self._single_constraints[END]:
            raise Exception('start time (%s) must be after end time (%s)'
                            % (self._single_constraints[START], self._single_constraints[END]))

    def _set_name_value(self, name, value):
        if not match('^[\w\*\?]*$', value):
            raise Exception('Illegal characters in "%s"' % value)
        found = None
        for key in self._multiple_constraints.keys():
            if key.startswith(name):
                if found:
                    raise Exception('Ambiguous parameter: %s' % name)
                else:
                    found = key
        if not found:
            raise Exception('Did not recognise "%s"' % name)
        self._multiple_constraints[found].append(value)

    def _build_query(self):
        sql, params = 'select ', []
        if self._flags[COUNT]:
            sql += 'count(*) '
        else:
            sql += ('''network, station, location, channel,
                       coalesce(timespans,'<' || starttime || ' ' || endtime || '>'), samplerate ''')
            if not self._flags[JOIN_QSR]:
                sql += ', quality '
        sql += 'from tsindex '
        constrained = False

        def conjunction(sql, constrained):
            if constrained:
                sql += 'and '
            else:
                sql += 'where '
                constrained = True
            return sql, constrained

        for name in self._multiple_constraints:
            repeated = False
            for value in self._multiple_constraints[name]:
                if not repeated:
                    sql, constrained = conjunction(sql, constrained)
                    sql += '( '
                    repeated = True
                else:
                    sql += 'or '
                sql += '%s like ? ' % name
                params.append(self._wildchars(value))
            if repeated:
                sql += ') '
        if self._single_constraints[START]:
            sql, constrained = conjunction(sql, constrained)
            sql += 'endtime > ?'
            params.append(self._single_constraints[START])
        if self._single_constraints[END]:
            sql, constrained = conjunction(sql, constrained)
            sql += 'starttime < ?'
            params.append(self._single_constraints[END])
        return sql, tuple(params)

    @staticmethod
    def _wildchars(value):
        return sub(r'\?', '_', sub(r'\*', '%', value))

    def _count(self, sql, params, stdout):
        # force to int here to avoid issues with strings on python 2
        print(int(self.fetchsingle(sql, params)), file=stdout)

    def _rows(self, sql, params, stdout):
        self._log.debug('%s %s' % (sql, params))
        builder = MultipleSNCLBuilder(self._log, self._timespan_tol, self._timespan_inc,
                                      self._flags[JOIN] or self._flags[JOIN_QSR])

        def callback(row):
            if self._flags[JOIN_QSR]:
                n, s, l, c, ts, r = row
                builder.add_timespans('%s_%s_%s_%s' % (n, s, l, c), ts, r)
            else:
                n, s, l, c, ts, r, q = row
                builder.add_timespans('%s_%s_%s_%s_%s (%g Hz)' % (n, s, l, c, q, r), ts, r)

        self.foreachrow(sql, params, callback)
        print()
        for coverage in builder.coverages():
            print('  %s' % coverage.sncl)
            for ts in coverage.timespans:
                print('    %s - %s' % (format_epoch(ts[0]), format_epoch(ts[1])))
            print()
