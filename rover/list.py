
from re import match, sub

from .sqlite import Sqlite


class IndexLister(Sqlite):
    """
    List entries in the index that match the given constraints.
    """

    def __init__(self, dbpath, log):
        super().__init__(dbpath, log)
        self._multiple_constraints = {'station': [],
                                      'network': [],
                                      'channel': [],
                                      'location': [],
                                      'quality': [],
                                      'samplerate': []}
        self._single_constraints = {'begin': None,
                                    'end': None}
        self._flags = {'count': False, 'join': False}

    def _display_help(self):
        print('''
        
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
    
  Examples:
  
    rover list-index IU.ANMO.00.BH? count
    
      will display the number of entries for all time, any
      quality or smaplerate.
      
    rover list-index net=* begin=2001-01-01
    
      will list all entries in the index after the year 2000.
      
  Note that console logging is to stderr, while results are
  printed to stdout.
''')

    def list(self, args):
        if not args:
            self._display_help()
        else:
            self._parse_args(args)
            sql, params = self._build_query()
            if self._flags['count']:
                self._count(sql, params)
            else:
                self._rows(sql, params)

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
                    if name in ('begin', 'end'):
                        self._set_time_limit(name, value)
                    else:
                        self._set_name_value(name, value)

    def _assert_unset_flags(self, name1):
        for name2 in self._flags:
            if self._flags[name2]:
                raise Exception('Cannot specify multiple keys (%s, %s)' % (name1, name2))

    def _set_snclq(self, snclq):
        components = snclq.split('.')
        if len(components) < 2 or len(components) > 5:
            raise Exception('Cannot parsee %s (expect 2 to 5 values separated by "." for SNCLQ) % snclq')
        self._set_name_value('network', components[0])
        self._set_name_value('station', components[1])
        if len(components) > 2: self._set_name_value('location', components[2])
        if len(components) > 3: self._set_name_value('channel', components[3])
        if len(components) > 4: self._set_name_value('quality', components[4])

    def _set_time_limit(self, name, value):
        if self._single_constraints[name]:
            raise Exception('Multiple values for %s' % name)
        if not match('\d{4}(-\d{2}(-\d{2}(T\d{2}(:\d{2}(:\d{2}(.\d{1,6})?)?)?)?)?)?', value):
            raise Exception('Poorly formed time "%s" (should be 2017, 2017-01-01T01:01:01.00 etc' % value)
        value = value + '2000-01-01T00:00:00.000000'[len(value):]
        self._log.debug('Padded time "%s"'% value)
        self._single_constraints[name] = value
        if self._single_constraints['begin'] and self._single_constraints['end'] \
                and self._single_constraints[begin] > self._single_constraints['end']:
            raise Exception('begin (%s) must be after end (%s)'
                            % (self._single_constraints['begin'], self._single_constraints['end']))

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
        if self._flags['count']:
            sql += 'count(*) '
        else:
            sql += 'network, station, location, channel, quality, samplerate, starttime, endtime '
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
        if self._single_constraints['begin']:
            sql += 'and endtime > ?'
            params.append(self._single_constraints['begin'])
        if self._single_constraints['end']:
            sql += 'and starttime > ?'
            params.append(self._single_constraints['end'])
        if not self._flags['count']:
            sql += 'order by network, station, location, channel, quality, samplerate, starttime'
        return sql, tuple(params)

    def _wildchars(self, value):
        return sub(r'\?', '_', sub(r'\*', '%', value))

    def _count(self, sql, params):
        print(self._fetchsingle(sql, params))

    def _rows(self, sql, params):
        self._log.debug('%s %s' % (sql, params))
        c = self._db.cursor()
        st, prev, join = None, None, self._flags['join']
        for row in c.execute(sql, params):
            if join:
                if not prev:
                    prev = row
                    st = prev[6]
                else:
                    if prev[0:5] == row[0:5]:
                        pass # todo check contig
                    else:
                        row = list(row)
                        row[6] = st
                        prev = None
                        print(*row)
            else:
                print(*row)


def list_index(args, log):
    IndexLister(args.mseed_db, log).list(args.args)

