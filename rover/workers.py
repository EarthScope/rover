
from subprocess import Popen
from time import sleep


class Workers:
    """
    A collection of processes that run asynchronously.  Note that the Python
    code here does NOT run asynchonously - it will block if there are no free
    workers.

    The idea is that we run N meedindex processes in the background so that
    we are not waiting on them to complete.
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


