from sqlite3 import connect


class NoResult(Exception): pass


class Sqlite():
    '''
    Utility class supporting various common database operations.
    '''

    def __init__(self, dbpath, log):
        self._log = log
        self._db = connect(dbpath)

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
            raise NoResult(sql)

    def _fetchall(self, sql, params=tuple()):
        c = self._db.cursor();
        return c.execute(sql, params).fetchall()
