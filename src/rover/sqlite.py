
from sqlite3 import connect

from .utils import canonify


"""
Support for database access.
"""


def init_db(dbpath, log):
    """
    Open a connection to the database.
    """

    log.debug('Connecting to sqlite3 %s' % dbpath)
    db = connect(dbpath, timeout=60.0)
    # https://www.sqlite.org/foreignkeys.html
    db.execute('PRAGMA foreign_keys = ON')
    db.execute('PRAGMA case_sensitive_like = ON')  # as used by mseedindex
    return db


class NoResult(Exception):
    """
    Exception thrown when no results available.
    """

    def __init__(self, sql, params):
        super().__init__('%s %s' % (sql, params))


class CursorContext:
    """
    Create a cursor for the duration of the scope (and then close it).
    """

    def __init__(self, support, quiet):
        self._support = support
        self._quiet = quiet
        self._cursor = support._db.cursor()

    def __enter__(self):
        return self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            if self._quiet:
                self._support._log.debug('Cursor exit: %s' % exc_val)
            else:
                self._support._log.error('Cursor exit: %s' % exc_val)
        else:
            self._support._db.commit()  # probably implied by close?
        self._cursor.close()
        return False  # propagate any exceptions


class SqliteDb:
    """
    Base class with utilities for accessing database.
    """

    def __init__(self, db, log):
        self._db = db
        self._log = log

    def cursor(self, quiet=False):
        return CursorContext(self, quiet)

    def execute(self, sql, params=tuple(), quiet=False):
        """
        Execute a single command in a transaction.
        """
        with self.cursor(quiet=quiet) as c:
            self._log.debug('Execute: %s %s' % (sql, params))
            c.execute(sql, params)

    def fetchsingle(self, sql, params=tuple(), quiet=False):
        """
        Return a single value from a select.

        Raise NoResult if no value.
        """
        with self.cursor(quiet=quiet) as c:
            self._log.debug('Fetchsingle: %s %s' % (sql, params))
            result = c.execute(sql, params).fetchone()
            if result:
                if len(result) > 1:
                    raise Exception('Multiple results for "%s %s"' % (sql, params))
                else:
                    return result[0]
            else:
                raise NoResult(sql, params)

    def fetchone(self, sql, params=tuple(), quiet=False):
        """
        Return a single row from a select.

        Raise NoResult if no row.
        """
        with self.cursor(quiet=quiet) as c:
            self._log.debug('Fetchone: %s %s' % (sql, params))
            result = c.execute(sql, params).fetchone()
            if result:
                return result
            else:
                raise NoResult(sql, params)

    def fetchall(self, sql, params=tuple(), quiet=False):
        """
        Return a list of rows from a select.

        Note that it may be better (eg in list-index) to iterate over
        the cursor explicitly (see foreachrow).
        """
        with self.cursor() as c:
            self._log.debug('Fetchall: %s %s' % (sql, params))
            return c.execute(sql, params).fetchall()

    def foreachrow(self, sql, params, callback, quiet=False):
        """
        Call the callback for each row in the results.
        """
        with self.cursor(quiet=quiet) as c:
            self._log.debug('foreachrow: %s %s' % (sql, params))
            for row in c.execute(sql, params):
                callback(row)

    def close(self):
        self._db.close()


class SqliteContext:
    """
    Create a database connection for the duration of the scope.
    """

    def __init__(self, file, log):
        self._db = SqliteDb(connect(file, timeout=60.0), log)

    def __enter__(self):
        return self._db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._db.close()
        return False  # propagate any exceptions


class SqliteSupport(SqliteDb):
    """
    Alternative constructor for SqliteDb.
    """

    def __init__(self, config):
        super().__init__(config.db, config.log)
