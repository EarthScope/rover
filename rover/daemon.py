
from .process import Processes
from .sqlite import SqliteSupport
from .utils import check_cmd, run
from .args import START, DAEMON, ROVERCMD


class Starter:
    """
    Start the background(daemon) process to support `rover subscribe`.

    See also `rover stop`.

##### Significant Parameters

@rover-cmd
    """

    def __init__(self, config):
        self._log = config.log
        self._rover_cmd = check_cmd(config.arg(ROVERCMD), 'rover', 'rover-cmd', config.log)

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
        self._log = config.log
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
        self._log = config.log

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % DAEMON)
