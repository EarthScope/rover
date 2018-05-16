
import sys
from re import match, sub

from .help import HelpFormatter
from .coverage import MultipleSNCLBuilder
from .sqlite import SqliteSupport
from .utils import format_epoch, SingleUse


"""
The 'rover list-index' command - display timespans from the local index.
"""


BEGIN = 'begin'
END = 'end'
COUNT = 'count'
JOIN = 'join'
JOIN_QSR = 'join-qsr'

STATION = 'station'
NETWORK = 'network'
CHANNEL = 'channel'
LOCATION = 'location'
QUALITY = 'quality'
SAMPLERATE = 'samplerate'


class IndexLister(SqliteSupport, SingleUse, HelpFormatter):
    """
### List Index

    rover list-index [net=...|sta=...|loc=...|cha=..|qua=...|samp=...]* \\
    [count|join|join-samplerates]

    rover list-index [S.N.C.L.Q]* [begin=...] [end=...] \\
    [count|join|join-samplerates]

List index entries for the local store (config parameter mseed-dir) that match the given constraints.

Note that console logging is to stderr, while the command results are listed to stdout.

#### SNCLQ and Samplerate

Query parameters can be named (network, station, location, channel, qualit, samplerate) and unambiguous abbreviations
are accepted.  Alternative SNCLQ can be supplied (which can be truncated on the right, but must contain at least one
period).

The wildcards '*' and '?' can be used.

#### Time Range

The 'begin' and 'end' parameters can be given only once.  They must be of the form YYYY-MM-DDTHH:MM:SS.SSSSSS
(may be truncated on the right).  They define a range of times over which the data must appear (at least partially)
to be included:

#### Flags

The following parameters are simple flags that change the output format.  They are mutually exclusive and take no
value:

  count - only the number of matches will be shown

  join - continguous time ranges will be joined

  join-samplerates - the maximal timespan across all samplerates is shown (as used by retrieve)

##### Significant Parameters

@timespan-tol
@mseed-db
@verbosity
@log-dir
@log-name
@log-verbosity

#### Examples

    rover list-index IU.ANMO.00.BH? count

will display the number of entries for all time, and any quality or smaplerate.

    rover list-index net=* begin=2001-01-01

will list all entries in the index after the year 2000.

"""

    def __init__(self, config):
        SqliteSupport.__init__(self, config)
        SingleUse.__init__(self)
        HelpFormatter.__init__(self, False)
        args = config.args
        self._timespan_tol = args.timespan_tol
        self._multiple_constraints = {STATION: [],
                                      NETWORK: [],
                                      CHANNEL: [],
                                      LOCATION: [],
                                      QUALITY: [],
                                      SAMPLERATE: []}
        self._single_constraints = {BEGIN: None,
                                    END: None}
        self._flags = {COUNT: False, JOIN: False, JOIN_QSR: False}

    def _display_help(self):
        self.print('''
The list_store command prints entries from the index that match 
the query parameters.  Parameters generally have the form 
name=value (no spaces).

The following parameters take '*' and '?' as wildcards, can be
repeated for multiple matches (combined with 'OR"), and the name
only has to match unambiguously (so cha=HHZ is OK):

  station, network, channel, location, quality, samplerate

The short form N.S.L.C.Q can also be used.

The following parameters can be given only once, must be of
the form YYYY-MM-DDTHH:MM:SS.SSSSSS (may be truncated on the
right), and define a range of times over which the block must 
appear (at least partially) to be included:

  begin, end

The following parameters are simple flags that change the
output format.  They are mutually exclusive and take no
value:

  count - only the number of matches will be shown

  join - continguous time ranges will be joined

  join-qsr - the maximal timespan across all quality and 
  samplerates is shown (as used by retrieve) 

Examples:

    rover list-index IU.ANMO.00.BH? count

will display the number of entries for all time, any
quality or smaplerate.

    rover list-index net=* begin=2001-01-01

will list all entries in the index after the year 2000.
  
Note that console logging is to stderr, while results are
printed to stdout.

''')

    def run(self, args, stdout=None):
        if not stdout: stdout = sys.stdout
        if not args:
            self._display_help()
        else:
            self._assert_single_use()
            self._parse_args(args)
            sql, params = self._build_query()
            if self._flags[COUNT]:
                self._count(sql, params, stdout=stdout)
            else:
                self._rows(sql, params, stdout=stdout)

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
                    if name in (BEGIN, END):
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
        components = snclq.split('.')
        if len(components) < 2 or len(components) > 5:
            raise Exception('Cannot parse %s (expect 2 to 5 values separated by "." for SNCLQ)' % snclq)
        self._set_name_value(NETWORK, components[0])
        self._set_name_value(STATION, components[1])
        if len(components) > 2: self._set_name_value(LOCATION, components[2])
        if len(components) > 3: self._set_name_value(CHANNEL, components[3])
        if len(components) > 4: self._set_name_value(QUALITY, components[4])

    def _set_time_limit(self, name, value):
        if self._single_constraints[name]:
            raise Exception('Multiple values for %s' % name)
        if not match('^\d{4}(-\d{2}(-\d{2}(T\d{2}(:\d{2}(:\d{2}(.\d{1,6})?)?)?)?)?)?$', value):
            raise Exception('Poorly formed time "%s" (should be 2017, 2017-01-01T01:01:01.00 etc' % value)
        value = value + '2000-01-01T00:00:00.000000'[len(value):]
        self._log.debug('Padded time "%s"'% value)
        self._single_constraints[name] = value
        if self._single_constraints[BEGIN] and self._single_constraints[END] \
                and self._single_constraints[BEGIN] > self._single_constraints[END]:
            raise Exception('begin (%s) must be after end (%s)'
                            % (self._single_constraints[BEGIN], self._single_constraints[END]))

    def _set_name_value(self, name, value):
        if not match('^[\w\*\?]+$', value):
            raise Exception('Illegal characters in "%s"' % value)
        found = None
        for key in self._multiple_constraints.keys():
            if key.startswith(name):
                if found:
                    raise Exception('Ambiguous parameter: %s' % name)
                else:
                    found = key
        self._multiple_constraints[found].append(value)

    def _build_query(self):
        sql, params = 'select ', []
        if self._flags[COUNT]:
            sql += 'count(*) '
        else:
            sql += 'network, station, location, channel, timespans, samplerate '
            if not self._flags[JOIN_QSR]:
                sql += ', quality '
        sql += 'from tsindex '
        constrained = False
        for name in self._multiple_constraints:
            repeated = False
            for value in self._multiple_constraints[name]:
                if not repeated:
                    if constrained:
                        sql += 'and '
                    else:
                        sql += 'where '
                        constrained = True
                    sql += '( '
                    repeated = True
                else:
                    sql += 'or '
                sql += '%s like ? ' % name
                params.append(self._wildchars(value))
            if repeated:
                sql += ') '
        if self._single_constraints[BEGIN]:
            sql += 'and endtime > ?'
            params.append(self._single_constraints[BEGIN])
        if self._single_constraints[END]:
            sql += 'and starttime < ?'
            params.append(self._single_constraints[END])
        return sql, tuple(params)

    @staticmethod
    def _wildchars(value):
        return sub(r'\?', '_', sub(r'\*', '%', value))

    def _count(self, sql, params, stdout):
        print(self.fetchsingle(sql, params), file=stdout)

    def _rows(self, sql, params, stdout):
        self._log.debug('%s %s' % (sql, params))
        builder = MultipleSNCLBuilder(self._log, self._timespan_tol, self._flags[JOIN] or self._flags[JOIN_QSR])

        def callback(row):
            if self._flags[JOIN_QSR]:
                n, s, l, c, ts, r = row
                builder.add_timespans('%s.%s.%s.%s' % (n, s, l, c), ts, r)
            else:
                n, s, l, c, ts, r, q = row
                builder.add_timespans('%s.%s.%s.%s.%s (%g Hz)' % (n, s, l, c, q, r), ts, r)

        self.foreachrow(sql, params, callback)
        print()
        for coverage in builder.coverages():
            print('  %s' % coverage.sncl)
            for ts in coverage.timespans:
                print('    %s - %s' % (format_epoch(ts[0]), format_epoch(ts[1])))
            print()
