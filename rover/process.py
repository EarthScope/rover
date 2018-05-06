
from os import getpid, kill

from .sqlite import SqliteSupport


class Processes(SqliteSupport):

    def __init__(self, config):
        super().__init__(config)
        self._create_processes_table()

    def _create_processes_table(self):
        self._execute('''create table if not exists rover_processes (
                           id integer primary key autoincrement,
                           pid integer unique,
                           name text not null,
                           creation_epoch int default (cast(strftime('%s', 'now') as int))
        )''')

    def assert_singleton(self, name):
        pid = getpid()
        c = self._db.cursor()
        try:
            result = c.execute('select pid from rover_processes where name like ?', (name,)).fetchone()
            if result:
                other = result[0]
                try:
                    kill(other, 0)
                    raise Exception('A %s process already exists' % name)
                except OSError:
                    self._log.warn('Cleaning out old entry for PID %d' % other)
                    c.execute('delete from rover_processes where pid = ?', (other, ))
            c.execute('insert into rover_processes (pid, name) values (?, ?)', (pid, name))
        finally:
            self._db.commit()
            c.close()

    def remove_process(self):
        pid = getpid()
        self._execute('delete from rover_processes where pid = ?', (pid,))
