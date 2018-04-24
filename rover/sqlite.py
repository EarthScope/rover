from sqlite3 import connect


class NoResult(Exception):

    def __init__(self, sql, params):
        super().__init__('%s %s' % (sql, params))



class Sqlite():
    '''
    Utility class supporting various common database operations.
    '''

    def __init__(self, dbpath, log):
        self._log = log
        self._db = connect(dbpath)
        # https://www.sqlite.org/foreignkeys.html
        self._execute('PRAGMA foreign_keys = ON')

    def _execute(self, sql, params=tuple()):
        c = self._db.cursor()
        c.execute(sql, params)
        self._db.commit()

    def _fetchsingle(self, sql, params=tuple()):
        c = self._db.cursor();
        result = c.execute(sql, params).fetchone()
        if result:
            if len(result) > 1:
                raise Exception('Multiple results for "%s %s"' % (sql, params))
            else:
                return result[0]
        else:
            raise NoResult(sql, params)

    def _fetchone(self, sql, params=tuple()):
        c = self._db.cursor();
        result = c.execute(sql, params).fetchone()
        if result:
            return result
        else:
            raise NoResult(sql, params)

    def _fetchall(self, sql, params=tuple()):
        c = self._db.cursor();
        return c.execute(sql, params).fetchall()
