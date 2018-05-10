
from subprocess import Popen
from time import sleep


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
        self._workers.append((command, Popen(command, shell=True), callback))

    def _wait_for_space(self):
        while True:
            self.check()
            if len(self._workers) < self._n_workers:
                self._log.debug('Space for new worker')
                return
            sleep(0.1)

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


class NoConflictWorkers(Workers):
    """
    Extend the above to block attempts to have two processes for the same key
    (typically SNCL and day, or the path to the file in the store).  This avoid
    simultaneous modification of the file by mutliple processes without using file
    locking (which is has problems with NFS, isn't great cross-platform, and wouldn't
    play well with Compacter which rewrites files).
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
        self._workers.append((command, Popen(command, shell=True),
                              lambda cmd, rtn: self._unlocking_callback(cmd, rtn, callback, key)))

    def execute(self, command, callback=None):
        raise Exception('Use execute_wit_lock()')

    def _unlocking_callback(self, cmd, rtn, callback, key):
        self._log.debug('Unlocking %s' % key)
        self._locked.remove(key)
        if not callback:
            super()._default_callback(cmd, rtn)
        else:
            callback(cmd, rtn)
