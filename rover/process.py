
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
        # we don't need to check start, because the daemon it spawns will be checked, but
        # it's better to have the error early and visible to the user
        elif self._command in (DAEMON, START):
            self._check_daemon(self._command == DAEMON)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._command in (RETRIEVE, DAEMON):
            self._clean_entry(self._command)
        return False  # let any exception propagate

    def _check_retrieve(self):
        with self._db:  # single transaction
            self._db.cursor().execute('begin')
            self._assert_not(DAEMON,
                             'You cannot use rover %s while the %s is running (PID %%d).  Use rover %s to stop the daemon.' %
                             (RETRIEVE, DAEMON, STOP))
            self._assert_not(RETRIEVE, 'rover %s is already running (PID %%d).' % RETRIEVE)
            self._record_process(RETRIEVE)

    def _check_daemon(self, record):
        with self._db:  # single transaction
            self._db.cursor().execute('begin')
            self._assert_not(RETRIEVE,
                             'You cannot start the %s while rover %s is running (PID %%d).' % (DAEMON, RETRIEVE))
            self._assert_not(DAEMON, 'The %s is already running (PID %%d).' % DAEMON)
            if record:
                self._record_process(DAEMON)

    def _assert_not(self, command, msg):
        try:
            pid = self._pid(command)
            if process_exists(pid):
                raise Exception(msg % pid)
            else:
                self._clean_entry(command)
        except NoResult:
            pass

    def _pid(self, command):
        # inside a transaction so avoid helper methods
        cmd, params = 'select pid from rover_processes where command like ?', (command,)
        try:
            return next(self._db.execute(cmd, params))[0]
        except Exception as e:
            raise NoResult(cmd, params)

    def _clean_entry(self, command):
        # inside a transaction so avoid helper methods
        self._db.execute('delete from rover_processes where command like ?', (command,))

    def _record_process(self, command):
        # inside a transaction so avoid helper methods
        self._db.execute('insert into rover_processes (command, pid) values (?, ?)', (command, getpid()))

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
