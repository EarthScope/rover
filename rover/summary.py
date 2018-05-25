
import sys
from re import match, sub
from sqlite3 import OperationalError

from .index import BEGIN, END
from .utils import STATION, NETWORK, CHANNEL, LOCATION, format_epoch
from .args import SUMMARY, MSEEDDB
from .sqlite import SqliteSupport


"""
Commands related to the summary:

The 'rover summary' command - creates a summary of the tsindex table.
The 'rover list-summary' command - displays entries from the summary table.
"""


class Summarizer(SqliteSupport):
    """
### Summary

    rover summary

Create a summary of the index in the database.  This lists the overall span of data for each SNCL and can
be queries using `rover list-summary`.

##### Significant Parameters

@mseed-db
@verbosity
@log-dir
@log-name
@log-verbosity

##### Examples

    rover summary

will create the summary.


    """

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        if len(args):
            raise Exception('Usage: rover %s' % SUMMARY)
        self._log.info('Generating summary table')
        self.execute('drop table if exists tsindex_summary')
        self.execute('''create table tsindex_summary as
                            select network, station, location, channel, 
                            min(starttime) AS earliest, max(endtime) AS latest, 
                            datetime('now') as updt
                        from tsindex
                        group by 1,2,3,4''')


class SummaryLister(SqliteSupport):
    """
### List Summary

    rover list-summary [net=...|sta=...|loc=...|cha=..]* [begin=...] [end=...]

    rover list-index [S_N_C_L_Q]* [begin=...] [end=...]

List summary entries for the local store (config parameter mseed-dir) that match the given constraints.

Note that console logging is to stderr, while the command results are listed to stdout.

#### SNCL

Query parameters can be named (network, station, location, channel) and unambiguous abbreviations
are accepted.  Alternative SNCL can be supplied (which can be truncated on the right, but must contain at least one
period).

The wildcards '*' and '?' can be used.

#### Time Range

The 'begin' and 'end' parameters can be given only once.  They must be of the form YYYY-MM-DDTHH:MM:SS.SSSSSS
(may be truncated on the right).  They define a range of times over which the data must appear (at least partially)
to be included:

##### Significant Parameters

@mseed-db
@verbosity
@log-dir
@log-name
@log-verbosity

#### Examples

    rover list-summary net=* begin=2001-01-01

will list all entries in the index after the year 2000.

"""

    # this is suspiciously close to list-index, but teh differences are significant and
    # to make a common base class would likely have made things more opaque.

    def __init__(self, config):
        SqliteSupport.__init__(self, config)
        self._mseed_db = config.file_path(MSEEDDB)
        self._multiple_constraints = {STATION: [],
                                      NETWORK: [],
                                      CHANNEL: [],
                                      LOCATION: []}
        self._single_constraints = {BEGIN: None,
                                    END: None}

    def run(self, args, stdout=None):
        if not stdout:
            stdout = sys.stdout
        self._check_database()
        self._parse_args(args)
        sql, params = self._build_query()
        self._rows(sql, params, stdout=stdout)

    def _check_database(self):
        try:
            self.execute('select count(*) from tsindex_summary')
        except OperationalError:
            raise Exception('''Cannot access the summary table in the database (%s).  Bad configuration or summary not generated?''' % self._mseed_db)

    def _parse_args(self, args):
        for arg in args:
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

    def _set_snclq(self, snclq):
        components = snclq.split('_')
        if len(components) < 2 or len(components) > 4:
            raise Exception('Cannot parse %s (expect 2 to 4 values separated by "_" for SNCL)' % snclq)
        self._set_name_value(NETWORK, components[0])
        self._set_name_value(STATION, components[1])
        if len(components) > 2: self._set_name_value(LOCATION, components[2])
        if len(components) > 3: self._set_name_value(CHANNEL, components[3])

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
        sql, params = 'select network, station, location, channel, earliest, latest from tsindex_summary', []
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

    def _rows(self, sql, params, stdout):
        self._log.debug('%s %s' % (sql, params))

        def callback(row):
            n, s, l, c, b, e = row
            print('  %s %s %s %s %s %s' % (n, s, l, c, b, e))

        print()
        self.foreachrow(sql, params, callback)
        print()
