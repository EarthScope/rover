import json
import os

from subprocess import Popen
from time import sleep

from .args import TEMPDIR
from .utils import uniqueish, unique_filename

"""
Support for running multiple sub-processes.
"""

class Workers:
    """
    A collection of processes that run asynchronously.  Note that the Python
    code here does NOT run asynchonously - it will block if there are no free
    workers.

    The idea is that (for example) we run N mseedindex processes in the background
    so that we are not waiting on them to complete.
    """

    def __init__(self, config, n_workers):
        self._temp_dir = config.dir(TEMPDIR)
        self._log = config.log
        self._n_workers = n_workers
        self._workers = []  # (command, popen, callback)

    def execute(self, command, callback=None, feedback=None):
        """
        Execute the command in a separate process.
        """
        self._wait_for_space()

        if not callback:
            callback = self._default_callback

        if feedback:
            name = uniqueish('rover_worker_feedback', command)
            filename = unique_filename(os.path.join(self._temp_dir, name))

            try:
                feedback = open (filename, 'w+')
            except Exception as ex:
                raise Exception('Cannot open feedback file: %s' % ex)

        self._log.debug('Adding worker for "%s" (callback %s)' % (command, callback))
        self._workers.append((command, self._popen(command, feedback=feedback), callback, feedback))

    def _wait_for_space(self):
        while True:
            self.check()
            if self.has_space():
                self._log.debug('Space for new worker (%d/%d)' % (len(self._workers), self._n_workers))
                return
            sleep(0.1)

    def has_space(self):
        return len(self._workers) < self._n_workers

    def _default_callback(self, cmd, returncode, **kwargs):
        if returncode:
            raise Exception('"%s" returned %d' % (cmd, returncode))
        else:
            self._log.debug('"%s" succeeded' % (cmd,))

    def check(self):
        i = len(self._workers) - 1
        while i > -1:
            command, process, callback, feedback = self._workers[i]
            process.poll()
            if process.returncode is not None:
                self._log.debug('Calling callback %s (command %s)' % (callback, command))
                process_feedback = {}
                if feedback:
                    try:
                        feedback.seek(0, 0)
                        # Pulls string from the temp file rover_worker_feedback*
                        feedback_str = feedback.readline(-1)
                        process_feedback = json.loads(feedback_str)
                    except Exception as ex:
                        if os.path.getsize(feedback.name) > 0:
                            feedback.seek(0, 0)
                            self._log.error('Error processing feedback file: %s, first line: %s' % (ex, feedback.readline()))
                    finally:
                        feedback.close()
                        os.remove(feedback.name)
                if process_feedback:
                    callback(command, process.returncode, feedback=process_feedback)
                else:
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

    def _popen(self, command, feedback=None):
        return Popen(command, shell=True, stdout=feedback)
