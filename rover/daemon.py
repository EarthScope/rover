from sqlite3 import OperationalError
from time import sleep, time

from .process import ProcessManager
from .args import START, DAEMON, ROVERCMD, RECHECKPERIOD, PREINDEX, POSTSUMMARY, fail_early, FILE, STOP
from .config import write_config
from .download import DownloadManager
from .index import Indexer
from .sqlite import SqliteSupport
from .summary import Summarizer
from .utils import check_cmd, run, canonify


DAEMONCONFIG = 'rover_daemon_config'
DOWNLOADCONFIG = 'rover_download_config'


class Starter:
    """
    Start the background (daemon) process to support `rover subscribe`.

    See also `rover stop`, `rover status`.

##### Significant Parameters

@rover-cmd
    """

    def __init__(self, config):
        fail_early(config)
        self._log = config.log
        self._rover_cmd = check_cmd(config, ROVERCMD, 'rover')
        # don't clean this because it may be long-lived (it will be over-written on re-use)
        self._config_path = write_config(config, DAEMONCONFIG, verbosity=0)

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % START)
        run('%s %s -f %s &' % (self._rover_cmd, DAEMON, self._config_path), self._log, uncouple=True)


class Stopper:
    """
    Stop the background (daemon) process to support `rover subscribe`.

    See also `rover start`, `rover status`.
    """

    def __init__(self, config):
        self._log = config.log
        self._processes = ProcessManager(config)

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % STOP)
        self._processes.kill_daemon()


class StatusShower:
    """
    Show whether the daemon is running or not..

    See also `rover start`, `rover stop`.
    """

    def __init__(self, config):
        self._log = config.log
        self._processes = ProcessManager(config)

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % STOP)
        print()
        print(self._processes.daemon_status())
        print()




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
        self._pre_index = config.arg(PREINDEX)
        self._post_summary = config.arg(POSTSUMMARY)
        self._download_manager = DownloadManager(config, DOWNLOADCONFIG)
        self._recheck_period = config.arg(RECHECKPERIOD) * 60 * 60
        self._config = config

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % DAEMON)
        if self._pre_index:
            Indexer(self._config).run([])
        while True:
            try:
                id = self._find_next_subscription()
                self._add_subscription(id)
            except NoSubscription:
                if self._download_manager.is_idle():
                    sleep(60)
            self._download_manager.step()
            sleep(1)

    def _source_complete(self):
        if self._post_summary:
            Summarizer(self._config).run([])

    def _find_next_subscription(self):
        now = time()
        found = [0]

        def callback(row):
            id = row[0]
            self._log.debug('Candidate: subscription %d' % id)
            if not found[0]:
                if not self._download_manager.has_source(id):
                    found[0] = id

        try:
            self.foreachrow('''select id from rover_subscriptions
                                  where (last_check_epoch is NULL or last_check_epoch < ?)
                                  order by creation_epoch''', (now - self._recheck_period,),
                            callback, quiet=True)
        except OperationalError:
            pass  # no table exists, so no data

        if found[0]:
            return found[0]
        else:
            raise NoSubscription()

    def _add_subscription(self, id):
        try:
            path, availability_url, dataselect_url = self.fetchone(
                '''select file, availability_url, dataselect_url from rover_subscriptions where id = ?''', (id,))
            self._log.info('Adding subscription %d (%s, %s)' % (id, availability_url, dataselect_url))
            self._download_manager.add(id, path, availability_url, dataselect_url, self._source_complete)
        finally:
            self.execute('''update rover_subscriptions set last_check_epoch = ? where id = ?''', (time(), id))
