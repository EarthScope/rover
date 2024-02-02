
from os import getpid, kill

from .args import RETRIEVE, DAEMON, START, STOP, UNSUBSCRIBE
from .sqlite import SqliteSupport, NoResult
from .utils import process_exists


"""
Process management (mainly stopping duplicate data by refusing to run retrieve and the daemon in parallel).
"""


class ProcessManager(SqliteSupport):

    def __init__(self, config):
        super().__init__(config)
        self._command = config.command
        self._create_processes_table()

    def _create_processes_table(self):
        self.execute('''CREATE TABLE IF NOT EXISTS rover_processes (
                           id integer primary key autoincrement,
                           pid integer unique,
                           command text not null,
                           creation_epoch int default (cast(strftime('%s', 'now') AS int))
        )''')

    def __enter__(self):
        """
        Check whether the command should run
        """
        # retrieve and the daemon cannot run in parallel because they may try to
        # update the same data.
        # unsubscribe requires that teh daemon be stopped since it may currently be
        # being processed.
        # any other command is either harmless (list...) or likely done by an expert user
        self._log.debug('Process check %s' % self._command)
        if self._command in (RETRIEVE, UNSUBSCRIBE):
            self._check_command(self._command)
        # we don't need to check start, because the daemon it spawns will be checked, but
        # it's better to have the error early and visible to the user
        elif self._command in (DAEMON, START):
            self._check_daemon(self._command == DAEMON)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._command in (RETRIEVE, DAEMON):
            self._clean_entry(self._command)
        return False  # let any exception propagate

    def _current_command_inside_transaction(self):
        pid, command = None, None
        rows = self._db.execute('SELECT pid, command FROM rover_processes', tuple())
        try:
            pid, candidate = next(rows)
            if process_exists(pid):
                command = candidate
                self._log.debug('Current process is %s/%d' % (command, pid))
            else:
                self._log.debug('Removing dead process %s/%d' % (candidate, pid))
                self._db.execute('DELETE FROM rover_processes WHERE pid = ?', (pid,))
        except StopIteration:
            pass  # table is empty
        try:
            next(rows)
            raise Exception('Multiple entries in rover_processes')
        except StopIteration:
            pass  # no more entries
        return pid, command

    def _record_process_inside_transaction(self, command):
        self._log.debug('Record new process %s/%d' % (command, getpid()))
        self._db.execute('INSERT INTO rover_processes (command, pid) VALUES (?, ?)', (command, getpid()))

    def _check_command(self, name):
        error = None
        with self._db:  # single transaction
            self._db.cursor().execute('BEGIN')
            pid, command = self._current_command_inside_transaction()
            if command == DAEMON:
                error = Exception(('You cannot use rover %s while the %s is running (PID %d). ' +
                                   'Use "rover %s" to stop the daemon.') %  (name, DAEMON, pid, STOP))
            elif command == RETRIEVE:
                error = Exception('rover %s is already running (PID %d).' % (RETRIEVE, pid))
            else:
                self._record_process_inside_transaction(RETRIEVE)
        # transaction closed
        if error:
            raise error

    def _check_daemon(self, record):
        error = None
        with self._db:  # single transaction
            self._db.cursor().execute('BEGIN')
            pid, command = self._current_command_inside_transaction()
            if command == RETRIEVE:
                error = Exception('You cannot use the %s while rover %s is running (PID %d). ' %
                                  (DAEMON, RETRIEVE, pid))
            elif command == DAEMON:
                error = Exception('The %s is already running (PID %d).' % (DAEMON, pid))
            elif record:
                self._record_process_inside_transaction(DAEMON)
        # transaction closed
        if error:
            raise error

    def _delete_command_inside_transaction(self, command):
        self._db.execute('DELETE FROM rover_processes WHERE command LIKE ?', (command,))

    def _clean_entry(self, command):
        with self._db:
            self._db.cursor().execute('BEGIN')
            self._delete_command_inside_transaction(command)

    def current_command(self):
        with self._db:
            self._db.cursor().execute('BEGIN')
            pid, command = self._current_command_inside_transaction()
            return pid, command

    def _pid_inside_transaction(self, command):
        cmd, params = 'SELECT pid FROM rover_processes WHERE command LIKE ?', (command,)
        try:
            pid = next(self._db.execute(cmd, params))[0]
            if process_exists(pid):
                return pid
            else:
                self._delete_command_inside_transaction(command)
        except Exception:
            pass
        raise NoResult(cmd, params)

    def kill_daemon(self):
        """
        Kill the daemon, if it exists.
        """
        try:
            with self._db:
                self._db.cursor().execute('BEGIN')
                pid = self._pid_inside_transaction(DAEMON)
                self._log.default('Killing %s (pid %d)' % (DAEMON, pid))
                kill(pid, 9)
                self._delete_command_inside_transaction(DAEMON)
        except NoResult:
            raise Exception('The %s is not running' % DAEMON)

    def daemon_status(self):
        with self._db:
            try:
                self._db.cursor().execute('BEGIN')
                pid = self._pid_inside_transaction(DAEMON)
                return 'The %s is running (process %d)' % (DAEMON, pid)
            except NoResult:
                return 'The %s is not running' % DAEMON

