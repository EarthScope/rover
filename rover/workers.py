from os import O_WRONLY, open
from subprocess import Popen
from time import sleep
import sys
import subprocess


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
                self._log.debug('Space for new worker (%d/%d)' % (len(self._workers), self._n_workers))
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
        from .manager import ErrorStatistics
        self.errors = ErrorStatistics()
        p = Popen([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, errors = p.communicate()
        # Print statement is used to add bytes to the output pipe. Semi-kluge but works until we find a better solution.
        # Potentially associated with the asynchronous behavior of the workers downloads.
        print("\033[F")
        # Determines if bytes are returned by the subprocess created by workers.execute.
        if len(output) is not 0:
            ErrorStatistics.bytecount += 1 #Increments the byte count in manager.ErrorStatistics
        return p