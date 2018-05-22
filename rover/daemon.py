
from .process import Processes
from .sqlite import SqliteSupport
from .utils import check_cmd, run
from .args import START, DAEMON


class Starter:
    """
    Start the background(daemon) process to support `rover subscribe`.

    See also `rover stop`.

##### Significant Parameters

@rover-cmd
    """

    def __init__(self, config):
        log, args = config.log, config.args
        self._log = log
        check_cmd('%s -h' % args.rover_cmd, 'rover', 'rover-cmd', log)
        self._rover_cmd = args.rover_cmd

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % START)
        run('%s &' % self._rover_cmd, self._log)


class Stopper:
    """
    Stop the background(daemon) process to support `rover subscribe`.

    See also `rover start`.
    """

    def __init__(self, config):
        log, args = config.log, config.args
        self._log = log
        self._processes = Processes(config)

    def run(self, args):
        self._processes.kill(DAEMON)


class Daemon(SqliteSupport):
    """
    The background process that supports `rover subscribe`.

    Do not run this command directly.  Instead use `rover stop` and `rover start`.
    """

    def __init__(self, config):
        super().__init__(config)
        log, args = config.log, config.args
        self._log = log

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % DAEMON)
