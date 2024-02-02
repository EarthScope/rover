
import sys
from re import match, sub
from sqlite3 import OperationalError

from .config import timeseries_db
from .index import START, END
from .utils import STATION, NETWORK, CHANNEL, LOCATION, format_epoch, tidy_timestamp
from .args import SUMMARY
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

Creates a summary of the index stored in a ROVER repository. This lists the
overall span of data for each Net_Sta_Loc_Chan and can be queried using
`rover list-summary`.

##### Significant Options

@data-dir
@verbosity
@log-dir
@log-verbosity

##### Examples

    rover summary

will create the summary of a local ROVER repository.


    """

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        if len(args):
            raise Exception('Usage: rover %s' % SUMMARY)
        self._log.info('Generating summary table')
        self.execute('DROP TABLE IF EXISTS tsindex_summary')
        try:
            self.execute('''CREATE TABLE tsindex_summary AS
                              SELECT network, station, location, channel,
                                     min(starttime) AS earliest, max(endtime) AS latest,
                                     datetime('now') AS updt
                              FROM tsindex
                              GROUP BY 1,2,3,4''')
        except OperationalError:
            self._log.default('No index found')


class SummaryLister(SqliteSupport):
    """
### List Summary

    rover list-summary [net=...|sta=...|loc=...|cha=..]* [start=...] [end=...]

    rover list-summary [N_S_L_C_Q]* [start=...] [end=...]

List a summary of entries for a ROVER repository, defined by the data-dir
configuration option, that match given constraints. List summary is faster
than `rover list-index` but gives less detail. For more information,
run "rover list-index" with no arguments.

##### Significant Options

@data-dir
@verbosity
@log-dir
@log-verbosity

#### Examples

    rover list-summary net=* start=2001-01-01

list all entries in the summary after 2001-01-01.

"""

    # this is suspiciously close to list-index, but the differences are significant and
    # to make a common base class would likely have made things more opaque.

    def __init__(self, config):
        SqliteSupport.__init__(self, config)
        self._timeseries_db = timeseries_db(config)
        self._multiple_constraints = {STATION: [],
                                      NETWORK: [],
                                      CHANNEL: [],
                                      LOCATION: []}
        self._single_constraints = {START: None,
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
            self.execute('SELECT count(*) FROM tsindex_summary')
        except OperationalError:
            raise Exception('''Cannot access the summary table in the database (%s).  Bad configuration or summary not generated?''' % self._timeseries_db)

    def _parse_args(self, args):
        for arg in args:
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

    def _set_snclq(self, snclq):
        components = snclq.split('_')
        if len(components) < 2 or len(components) > 4:
            raise Exception('Cannot parse %s (expect 2 to 4 values separated by "_" for N_S_L_C)' % snclq)
        self._set_name_value(NETWORK, components[0])
        self._set_name_value(STATION, components[1])
        if len(components) > 2: self._set_name_value(LOCATION, components[2])
        if len(components) > 3: self._set_name_value(CHANNEL, components[3])

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
                    raise Exception('Ambiguous option: %s' % name)
                else:
                    found = key
        self._multiple_constraints[found].append(value)

    def _build_query(self):
        sql, params = 'SELECT network, station, location, channel, earliest, latest FROM tsindex_summary ', []
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
            sql += 'latest > ?'
            params.append(self._single_constraints[START])
        if self._single_constraints[END]:
            sql, constrained = conjunction(sql, constrained)
            sql += 'earliest < ?'
            params.append(self._single_constraints[END])
        return sql, tuple(params)

    @staticmethod
    def _wildchars(value):
        return sub(r'\?', '_', sub(r'\*', '%', value))

    def _rows(self, sql, params, stdout):
        self._log.debug('%s %s' % (sql, params))

        def callback(row):
            n, s, l, c, b, e = row
            print('  %s_%s_%s_%s %s %s' % (n, s, l, c, b, e))

        print()
        self.foreachrow(sql, params, callback)
        print()
