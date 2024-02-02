
from sqlite3 import OperationalError
from time import sleep, time

from rover import __version__
from .args import START, DAEMON, ROVERCMD, RECHECKPERIOD, PREINDEX, POSTSUMMARY, fail_early, STOP, UserFeedback, \
    FORCECMD
from .config import write_config
from .manager import DownloadManager
from .report import Reporter
from .index import Indexer
from .process import ProcessManager
from .sqlite import SqliteSupport
from .summary import Summarizer
from .utils import check_cmd, run, windows

"""
Commands related to the daemon:

The 'rover daemon' command - equivalent to related retrieval, but in the background.
The 'rover start' command - start the daemon,
The 'rover status' command - show whether the dameon is running.
The 'rover stop' command - stop teh daemon.
"""


DAEMONCONFIG = 'rover_daemon_config'
DOWNLOADCONFIG = 'rover_download_config'


class Starter(UserFeedback):
    """
### Start

Starts the background, daemon, process to support `rover subscribe`. The
option, --recheck-period, sets the time interval in hours for the daemon to
reprocess. ROVER start is the preferred method to initiate the retrieval of
data via subscription(s).

See also `rover stop`, `rover status` and `rover daemon`.

##### Significant Options

@rover-cmd
@mseedindex-cmd
@download-workers
@mseedindex-workers
@temp-dir
@subscriptions-dir
@recheck-period
@download-retries
@http-timeout
@http-retries
@web
@http-bind-address
@http-port
@email
@email-from
@smtp-address
@smtp-port
@verbosity
@log-dir
@log-verbosity
@dev

In addition, options relevant to the processing pipeline (see `rover retrieve`
, or the individual commands for download, ingest and index) apply.

##### Examples

    rover start -f roverrc

will start the daemon using the given configuration file.

    rover start --recheck-period 24

will start the daemon, processing subscriptions every 24 hours.

    """

    def __init__(self, config):
        UserFeedback.__init__(self, config)
        fail_early(config)
        self._rover_cmd = check_cmd(config, ROVERCMD, 'rover')
        # don't clean this because it may be long-lived (it will be over-written on re-use)
        self._config_path = write_config(config, DAEMONCONFIG, verbosity=0)

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % START)
        if windows():
            run('%s %s -f %s' % ('pythonw -m rover', DAEMON, self._config_path), self._log, uncouple=True)
        else:
            run('%s %s -f %s' % (self._rover_cmd, DAEMON, self._config_path), self._log, uncouple=True)
        self._log.default('ROVER version %s - starting %s' % (__version__, DAEMON))
        self.display_feedback()


class Stopper:
    """
### Stop

Stop the background, daemon, process to support `rover subscribe`.

See also `rover start`, `rover status`.

##### Significant Options

@verbosity
@log-dir
@log-verbosity

##### Examples

    rover stop -f roverrc

will stop the daemon that was started using the given configuration file.

    """

    def __init__(self, config):
        self._log = config.log
        self._processes = ProcessManager(config)

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % STOP)
        self._processes.kill_daemon()  # logs suitable message


class StatusShower:
    """
### Status

Displays if the daemon is operating.

See also `rover start`, `rover stop`.

##### Significant Options

@verbosity
@log-dir
@log-verbosity

##### Examples

    rover status -f roverrc

will show whether a daemon, using a given configuration file, is running.

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
### Daemon

The background, daemon, process that supports `rover subscribe`. ROVER's start
command is the preferred method to launch the subscription service.

See also `rover stop`, `rover status`.

##### Significant Options

@rover-cmd
@mseedindex-cmd
@download-workers
@mseedindex-workers
@temp-dir
@subscriptions-dir
@recheck-period
@download-retries
@http-timeout
@http-retries
@web
@http-bind-address
@http-port
@email
@email-from
@smtp-address
@smtp-port
@verbosity
@log-dir
@log-verbosity
@dev

##### Examples

    rover daemon -f roverrc

will start the daemon in the foreground using the given configuration file.

    rover start --recheck-period 24

will start the daemon in the foreground, processing subscriptions every 24 hours.

REMINDER: ROVER start is the preferred method to launch the subscription service.

    """

    def __init__(self, config):
        super().__init__(config)
        self._log = config.log
        self._pre_index = config.arg(PREINDEX)
        self._post_summary = config.arg(POSTSUMMARY)
        self._download_manager = DownloadManager(config, DOWNLOADCONFIG)
        self._recheck_period = config.arg(RECHECKPERIOD) * 60 * 60
        self._reporter = Reporter(config)
        self._config = config

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % DAEMON)
        if self._pre_index:
            Indexer(self._config).run([])
        while True:
            try:
                try:
                    id = self._find_next_subscription()
                    self._add_subscription(id)
                except NoSubscription:
                    if self._download_manager.is_idle():
                        sleep(60)
                self._download_manager.step()
                sleep(1)
            except Exception as e:
                self._reporter.send_email('ROVER Failure', self._reporter.describe_error(DAEMON, e))
                raise

    def _source_callback(self, source):
        self.execute('''UPDATE rover_subscriptions SET last_error_count = ?, consistent = ? WHERE id = ?''',
                     (source.errors.final_errors, source.consistent, source.name))
        if self._post_summary:
            Summarizer(self._config).run([])
        subject, msg = self._reporter.describe_daemon(source)
        self._reporter.send_email(subject, msg)

    def _find_next_subscription(self):
        now = time()
        found = [0]

        def callback(row):
            id = row[0]
            self._log.debug('Candidate: subscription %d' % id)
            if not found[0]:
                # todo - check this logic in test (try repeat while still downloading)
                if not self._download_manager.has_source(id):
                    found[0] = id

        try:
            self.foreachrow('''SELECT id FROM rover_subscriptions
                                  WHERE (last_check_epoch IS NULL OR last_check_epoch < ?)
                                  ORDER BY creation_epoch''', (now - self._recheck_period,),
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
                '''SELECT file, availability_url, dataselect_url FROM rover_subscriptions WHERE id = ?''', (id,))
            self._log.default('Adding subscription %d (%s, %s)' % (id, availability_url, dataselect_url))
            self._download_manager.add(id, path, True, availability_url, dataselect_url, self._source_callback)
        finally:
            self.execute('''UPDATE rover_subscriptions SET last_check_epoch = ? WHERE id = ?''', (time(), id))
