
from os import getpid, kill
from sqlite3 import OperationalError
from time import sleep

from .utils import format_epoch
from .sqlite import SqliteSupport


class DatabaseBasedLockFactory(SqliteSupport):

    def __init__(self, config, name):
        super().__init__(config)
        self._table_name = 'rover_lock_%s' % name
        self._config = config
        self._create_lock_table()

    def _create_lock_table(self):
        self.execute('''create table if not exists %s (
                           id integer primary key autoincrement,
                           pid integer unique,
                           key text unique,
                           creation_epoch int default (cast(strftime('%%s', 'now') as int))
        )''' % self._table_name)

    def lock(self, key):
        return LockContext(self._config, self._table_name, key)


class LockContext(SqliteSupport):

    def __init__(self, config, table, key):
        super().__init__(config)
        self._table = table
        self._key = key

    def __enter__(self):
        self.acquire()

    def acquire(self):
        while True:
            try:
                with self._db:  # commits or rolls back
                    c = self._db.cursor()
                    c.execute('begin')
                    if not c.execute('select count(*) from %s where key = ?' % self._table, (self._key,)).fetchone()[0]:
                        self._log.debug('Acquired lock on %s with %s' % (self._table, self._key))
                        c.execute('insert into %s (pid, key) values (?, ?)' % self._table, (getpid(), self._key))
                        return
            except OperationalError:
                pass  # database was locked
            if not self._clean():
                self._log.debug('Sleeping on lock %s with %s' % (self._table, self._key))
                sleep(1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False

    def release(self):
        self._log.debug('Releasing lock on %s with %s' % (self._table, self._key))
        self.execute('delete from %s where key = ?' % self._table, (self._key,))

    def _clean(self):
        cleaned = [False]

        def callback(row):
            pid, key, epoch = row
            try:
                kill(pid, 0)
            except OSError:
                self._log.warn('Cleaning out old entry for PID %d on lock %s with %s (created %s)' % (
                    pid, self._table, key, format_epoch(epoch)))
                self.execute('delete from %s where key = ?' % self._table, (self._key,))
                cleaned[0] = True

        self.foreachrow('select pid, key, creation_epoch from %s' % self._table, tuple(), callback)
        return cleaned[0]
