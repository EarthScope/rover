
from sqlite3 import OperationalError
from time import sleep, time

from .args import START, DAEMON, ROVERCMD, RECHECKPERIOD, PREINDEX, POSTSUMMARY, fail_early, STOP, UserFeedback, \
    FORCECMD, ROVER_VERSION
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

Start the background (daemon) process to support `rover subscribe`.

See also `rover stop`, `rover status` and `rover daemon`.

##### Significant Parameters

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

In addition, parameters relevant to the processing pipeline (see `rover retrieve`, or the individual commands
for download, ingest and index) will apply,

Logging for individual processes in the pipeline will automatically configured with `--unique-logs --log-verbosity 3`.
For most worker tasks, that will give empty logs (no warnings or errors), which will be automatically deleted
(see `rover download`).  To preserve logs, and to use the provided verbosity level, start the daemon with `--dev`,

When the daemon is running status should be visible at http://localhost:8000 (by default).  When a subscription
is processed an email can be sent to the user (if `--email` is used).

#### Errors, Retries and Consistency

If `download-retries` allows, subscriptions are re-processed until no errors occur and, once data appear to be complete,
an additional retrieval is made which should result in no data being downloaded.  If this is not the case - if
additional data are found - then the web services are inconsistent.

Errors and inconsistencies are reported in the logs and in the optional email (`email` parameter) sent to the user.

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
        self._log.default('Rover version %s - starting %s' % (ROVER_VERSION, DAEMON))
        self.display_feedback()


class Stopper:
    """
### Stop

Stop the background (daemon) process to support `rover subscribe`.

See also `rover start`, `rover status`.

##### Significant Parameters

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

Show whether the daemon is running or not..

See also `rover start`, `rover stop`.

##### Significant Parameters

@verbosity
@log-dir
@log-verbosity

##### Examples

    rover status -f roverrc

will show whether the daemon using the given configuration file is running.

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

The background (daemon) process that supports `rover subscribe`.

**Prefer using `rover start` to start this task in the background.**

See also `rover stop`, `rover status`.

##### Significant Parameters

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

In addition, parameters relevant to the processing pipeline (see `rover retrieve`, or the individual commands
for download, ingest and index) will apply,

Logging for individual processes in the pipeline will automatically configured with `--unique-logs --log-verbosity 3`.
For most worker tasks, that will give empty logs (no warnings or errors), which will be automatically deleted
(see `rover download`).  To preserve logs, and to use the provided verbosity level, start the daemon with `--dev`,

When the daemon is running status should be visible at http://localhost:8000 (by default).  When a subscription
is processed an email can be sent to the user (if `--email` is used).

#### Errors, Retries and Consistency

If `download-retries` allows, subscriptions are re-processed until no errors occur and, once data appear to be complete,
an additional retrieval is made which should result in no data being downloaded.  If this is not the case - if
additional data are found - then the web services are inconsistent.

Errors and inconsistencies are reported in the logs and in the optional email (`email` parameter) sent to the user.

##### Examples

    rover daemon -f roverrc

will start the daemon (in the foreground - see `rover start`) using the given configuration file.

    rover start --recheck-period 24

will start the daemon (in the foreground - see `rover start`), processing subscriptions every 24 hours.

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
                self._reporter.send_email('Rover Failure', self._reporter.describe_error(DAEMON, e))
                raise

    def _source_callback(self, source):
        self.execute('''update rover_subscriptions set last_error_count = ?, consistent = ? where id = ?''',
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
            self._log.default('Adding subscription %d (%s, %s)' % (id, availability_url, dataselect_url))
            self._download_manager.add(id, path, True, availability_url, dataselect_url, self._source_callback)
        finally:
            self.execute('''update rover_subscriptions set last_check_epoch = ? where id = ?''', (time(), id))
