
from os import O_WRONLY, open
from subprocess import Popen
from time import sleep

from .lock import DatabaseBasedLockFactory


"""
Support for running multiple sub-processes.
"""


class Workers:
    """
    A collection of processes that run asynchronously.  Note that the Python
    code here does NOT run asynchonously - it will block if there are no free
    workers.

    The idea is that (for example) we run N meedindex processes in the background
    so that we are not waiting on them to complete.
    """

    def __init__(self, config, n_workers):
        self._log = config.log
        self._n_workers = n_workers
        self._workers = []  # (command, popen, callback)

    def execute(self, command, callback=None):
        """
        Execute the command in a separate process.
        """
        self._wait_for_space()
        if not callback:
            callback = self._default_callback
        self._log.debug('Adding worker for "%s" (callback %s)' % (command, callback))
        self._workers.append((command, self._popen(command), callback))

    def _wait_for_space(self):
        while True:
            self.check()
            if self.has_space():
                self._log.debug('Space for new worker')
                return
            sleep(0.1)

    def has_space(self):
        return len(self._workers) < self._n_workers

    def _default_callback(self, cmd, returncode):
        if returncode:
            raise Exception('"%s" returned %d' % (cmd, returncode))
        else:
            self._log.debug('"%s" succeeded' % (cmd,))

    def check(self):
        i = len(self._workers) - 1
        while i > -1:
            command, process, callback = self._workers[i]
            process.poll()
            if process.returncode is not None:
                self._log.debug('Calling callback %s (command %s)' % (callback, command))
                callback(command, process.returncode)
                self._workers = self._workers[:i] + self._workers[i+1:]
            i -= 1

    def wait_for_all(self):
        """
        Wait for all remaining processes to finish.
        """
        while True:
            self.check()
            if not self._workers:
                self._log.debug('No workers remain')
                return
            sleep(0.1)

    def _popen(self, command):
        return Popen(command, shell=True)


class NoConflictPerProcessWorkers(Workers):
    """
    Extend the above to block attempts to have two processes for the same key
    (typically N_S_L_C and day, or the path to the file in the repository).  This avoids
    simultaneous modification of the file by multiple processes without using file
    locking (which is has problems with NFS, isn't great cross-platform, and used
    to cause issues with "compact" when we re-wrote files).
    """

    def __init__(self, config, n_workers):
        super().__init__(config, n_workers)
        # no need to protect this with a lock because we are single threaded
        self._locked = set()

    def execute_with_lock(self, command, key, callback=None):
        self._wait_for_space()
        count = 0
        while True:
            if key not in self._locked:
                self._log.debug('Locking  %s' % key)
                self._locked.add(key)
                break
            if count % 100 == 0:
                self._log.debug('Waiting for %s' % key)
                count += 1
            sleep(0.1)
            self.check()
        self._log.debug('Adding worker for "%s" (callback %s)' % (command, callback))
        self._workers.append((command, self._popen(command),
                              lambda cmd, rtn: self._unlocking_callback(cmd, rtn, callback, key)))

    def execute(self, command, callback=None):
        raise Exception('Use execute_with_lock()')

    def _unlocking_callback(self, cmd, rtn, callback, key):
        self._log.debug('Unlocking %s' % key)
        self._locked.remove(key)
        if not callback:
            super()._default_callback(cmd, rtn)
        else:
            callback(cmd, rtn)


class NoConflictPerDatabaseWorkers(Workers):
    """
    Extend the above to block attempts for two processes (workers) to access
    the same resource.  Because this uses a database table it works across
    processes.
    """

    def __init__(self, config, n_workers, name):
        super().__init__(config, n_workers)
        self._lock_factory = DatabaseBasedLockFactory(config, name)
        self._locks = {}

    def execute_with_lock(self, command, key, callback=None):
        # here we are locking for subprocess, so we need to supply the PID
        # after acquiring the lock.
        # note that we cannot deadlock even though this is single-threaded and blocks,
        # because this is called only by code that iterates through the items to be locked
        # (so doesn't contain duplicates).  any contention must be with another process.
        self._wait_for_space()
        self._locks[key] = self._lock_factory.lock(key)
        self._locks[key].acquire()
        try:
            popen = self._popen(command)
            self._locks[key].set_pid(popen.pid)
        except:  # don't let a null PID stay in the table
            self._locks[key].release()
            raise
        self._log.debug('Adding worker for "%s" (callback %s)' % (command, callback))
        self._workers.append((command, popen,
                              lambda cmd, rtn: self._unlocking_callback(cmd, rtn, callback, key)))

    def execute(self, command, callback=None):
        raise Exception('Use execute_with_lock()')

    def _unlocking_callback(self, cmd, rtn, callback, key):
        self._log.debug('Unlocking %s' % key)
        # again, this is single thread - the locking is across processes
        self._locks[key].release()
        self._locks[key] = None
        if not callback:
            super()._default_callback(cmd, rtn)
        else:
            callback(cmd, rtn)

