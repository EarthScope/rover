
from os import getpid
from sqlite3 import OperationalError, IntegrityError
from time import sleep
from .utils import format_epoch, process_exists
from .sqlite import SqliteSupport


"""
Locking of named resources via the database.
"""


# name used for locking the mseed data file
MSEED = "mseed"
# name used for locking the asdf data file
ASDF = "asdf"


class DatabaseBasedLockFactory(SqliteSupport):
    """
    Support locking against some string (eg name of file) via the database.
    We're trying to avoid file locking because of NFS and cross-platform issues, so use this instead.
    A new instance of the factory must be generated for each kind of resource locked.  Multiple instances
    can exist for the same kind of resource (in different processes) - that's the whole point.
    """

    def __init__(self, config, name):
        super().__init__(config)
        self._table_name = 'rover_lock_%s' % name
        self._config = config
        self._create_lock_table()

    def _create_lock_table(self):
        self.execute('''CREATE TABLE IF NOT EXISTS %s (
                           id integer primary key autoincrement,
                           pid integer unique,
                           key text unique,
                           creation_epoch int default (cast(strftime('%%s', 'now') as int))
        )''' % self._table_name)

    def lock(self, key, pid=None):
        return LockContext(self._config, self._table_name, key, pid)


class LockContext(SqliteSupport):
    """
    Both context and acquire/release syntax are supported here.
    """

    def __init__(self, config, table, key, pid):
        super().__init__(config)
        self._table = table
        self._key = key
        self._pid = pid

    def __enter__(self):
        self.acquire()

    def acquire(self):
        clean = False
        while True:
            try:
                if clean:
                    if not self._clean():
                        self._log.debug('Sleeping on lock %s with %s' % (self._table, self._key))
                        sleep(1)
                # very careful with transactions here - want entire process to be in a single transaction
                with self._db:  # commits or rolls back
                    c = self._db.cursor()
                    c.execute('BEGIN')
                    if not c.execute('SELECT count(*) FROM %s WHERE key = ?' % self._table, (self._key,)).fetchone()[0]:
                        self._log.debug('Acquiring lock on %s with %s for PID %d' % (self._table, self._key, getpid()))
                        c.execute('INSERT INTO %s (pid, key) VALUES (?, ?)' % self._table, (self._pid, self._key))
                        return
            except IntegrityError as e:
                self._log.debug('Acquiring lock: %s' % e)
                sleep(1)
                pass  # PID existed and needs to be cleaned out
            except OperationalError as e:
                self._log.debug('Acquiring lock: %s' % e)
                sleep(1)
                pass  # database was locked
            clean = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False

    def set_pid(self, pid):
        self._log.debug('Setting PID on %s for %s to %d' % (self._table, self._key, pid))
        with self._db:
            c = self._db.cursor()
            c.execute('BEGIN')
            c.execute('UPDATE %s SET pid=? WHERE key=?' % self._table, (pid, self._key))

    def release(self):
        self._log.debug('Releasing lock on %s with %s' % (self._table, self._key))
        with self._db:
            c = self._db.cursor()
            c.execute('BEGIN')
            c.execute('DELETE FROM %s WHERE key = ?' % self._table, (self._key,))

    def _clean(self):
        cleaned = [False]

        def callback(row):
            pid, key, epoch = row
            if pid is not None and not process_exists(pid):
                # no longer a warning.  seems to occur when two transactions both
                # delete the same entry (one from the worker existing and one from a worker
                # waiting).  waiting starts the transaction before exiting, but completes
                # after, afaict (so the exiting has disappeared and the PID test succeeds
                # for the waiting),
                self._log.debug('Cleaning out old entry for PID %d on lock %s with %s (created %s)' % (
                    pid, self._table, key, format_epoch(epoch)))
                with self._db:
                    c = self._db.cursor()
                    c.execute('BEGIN')
                    c.execute('DELETE FROM %s WHERE key = ?' % self._table, (self._key,))
                    cleaned[0] = True

        self.foreachrow('SELECT pid, key, creation_epoch FROM %s' % self._table, tuple(), callback)
        return cleaned[0]
