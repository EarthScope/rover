from time import sleep, time

from .download import DownloadManager
from .process import Processes
from .sqlite import SqliteSupport
from .utils import check_cmd, run
from .args import START, DAEMON, ROVERCMD, RECHECKPERIOD


class Starter:
    """
    Start the background (daemon) process to support `rover subscribe`.

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
        run('%s %s &' % (self._rover_cmd, DAEMON), self._log)


class Stopper:
    """
    Stop the background (daemon) process to support `rover subscribe`.

    See also `rover start`.
    """

    def __init__(self, config):
        self._log = config.log
        self._processes = Processes(config)

    def run(self, args):
        self._processes.kill(DAEMON)


# todo - status command


DAEMONCONFIG = 'rover_daemon_config'


class NoSubscription(Exception):
    """
    No suitable subscription found while scanning the database.
    """


class Daemon(SqliteSupport):
    """
    The background process that supports `rover subscribe`.

    Prefer `rover stop` and `rover start` to using this command directly.
    """

    def __init__(self, config):
        super().__init__(config)
        self._log = config.log
        self._download_manager = DownloadManager(config, DAEMONCONFIG)
        self._recheck_period = config.arg(RECHECKPERIOD) * 60 * 60

    # todo - housekeeping like global index, summary, etc

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % DAEMON)
        while True:
            try:
                id = self._find_next_subscription()
                self._add_subscription(id)
            except NoSubscription:
                if self._download_manager.is_idle():
                    sleep(60)
            self._download_manager.step()
            sleep(1)

    def _find_next_subscription(self):
        now = time()
        found = [0]

        def callback(row):
            if not found[0]:
                id = row[0]
                if self._download_manager.has_source(id):
                    found[0] = id

        self.foreachrow('''select id from rover_subscriptions
                              where (last_check_epoch is NULL or last_check_epoch < ?)
                              order by creation_epoch''', (now - self._recheck_period),
                        callback)

        if found[0]:
            return found[0]
        else:
            raise NoSubscription()

    def _add_subscription(self, id):
        # todo - set last_check_epoch
        pass