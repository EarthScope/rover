
from os import getpid, kill

from .utils import process_exists
from .args import RETRIEVE, DAEMON, START, STOP
from .sqlite import SqliteSupport, NoResult


"""
Process management (daemons, the command line process etc).
"""


class ProcessManager(SqliteSupport):

    def __init__(self, config):
        super().__init__(config)
        self._command = config.command
        self._create_processes_table()

    def _create_processes_table(self):
        self.execute('''create table if not exists rover_processes (
                           id integer primary key autoincrement,
                           pid integer unique,
                           command text not null,
                           creation_epoch int default (cast(strftime('%s', 'now') as int))
        )''')

    def __enter__(self):
        """
        Check whether the command should run
        """
        # we only care about whether retieve and the daemon run in parallel
        # any other command is either harmless (list...) or likely done by an expert user.
        # but retrieve in parallel with daemon can result in duplicate data.
        self._log.debug('Process check %s' % self._command)
        if self._command == RETRIEVE:
            self._check_retrieve()
        # we don't nede to check start, because the daemon it spawns will be checked, but
        # it's better to have the error early and visible to the user
        elif self._command in (DAEMON, START):
            self._check_daemon(self._command == DAEMON)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._command in (RETRIEVE, DAEMON):
            self._clean_entry(self._command)
        return False  # let any exception propagate

    def _check_retrieve(self):
        self._assert_not(DAEMON, RETRIEVE,
                         'You cannot use rover %s while the %s is running.  Use rover %s to stop the daemon' %
                         (RETRIEVE, DAEMON, STOP),
                         True)

    def _check_daemon(self, record):
        self._assert_not(RETRIEVE, DAEMON,
                         'You cannot start the %s while rover %s is running' % (DAEMON, RETRIEVE),
                         record)

    def _assert_not(self, other, command, msg, record):
        try:
            pid = self._pid(other)
            if process_exists(pid):
                raise Exception(msg)
            else:
                self._clean_entry(other)
        except NoResult:
            pass
        if record:
            self._record_process(command)

    def _record_process(self, command):
        self.execute('insert into rover_processes (command, pid) values (?, ?)', (command, getpid()))

    def _pid(self, command):
        return self.fetchsingle('select pid from rover_processes where command like ?', (command,), quiet=True)

    def _clean_entry(self, command):
        self.execute('delete from rover_processes where command like ?', (command,))

    def kill_daemon(self):
        """
        Kill the daemon, if it exists.
        """
        try:
            pid = self._pid(DAEMON)
            self._log.info('Killing %s (pid %d)' % (DAEMON, pid))
            kill(pid, 9)
        except NoResult:
            raise Exception('The %s is not running' % DAEMON)

    def daemon_status(self):
        try:
            pid = self._pid(DAEMON)
            if process_exists(pid):
                return 'The %s is running (process %d)' % (DAEMON, pid)
        except NoResult:
            pass
        return 'The %s is not running' % DAEMON
