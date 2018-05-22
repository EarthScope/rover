
from os import getpid, kill

from .sqlite import SqliteSupport, NoResult

"""
Process management (daemons, the command line process etc).

See also the workers module.
"""


class Processes(SqliteSupport):

    def __init__(self, config):
        super().__init__(config)
        self._create_processes_table()

    def _create_processes_table(self):
        self.execute('''create table if not exists rover_processes (
                           id integer primary key autoincrement,
                           pid integer unique,
                           name text not null,
                           creation_epoch int default (cast(strftime('%s', 'now') as int))
        )''')

    def add_singleton_me(self, name):
        pid = getpid()
        # single transaction
        with self._db:
            c = self._db.cursor()
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

    def remove_me(self):
        pid = getpid()
        self.execute('delete from rover_processes where pid = ?', (pid,))

    def kill(self, name):
        try:
            pid = self.fetchone('select pid from rover_processes where name like ?', (name,), quiet=True)
            self._log.info('Killing %s (pid %d)' % (name, pid))
            kill(pid, 9)
        except NoResult:
            self._log.warn('No %s to kill' % name)
