
from shutil import copyfile
from sqlite3 import OperationalError

from .request import RequestComparison
from .manager import DownloadManager
from .args import SUBSCRIBE, LIST_SUBSCRIBE, UNSUBSCRIBE, SUBSCRIPTIONSDIR, AVAILABILITYURL, DATASELECTURL, DEV, \
    FORCEREQUEST, mm, TRIGGER, VERBOSITY, NO, DELETEFILES, TEMPDIR
from .sqlite import SqliteSupport, NoResult
from .utils import unique_path, build_file, format_day_epoch, safe_unlink, format_time_epoch, log_file_contents, \
    fix_file_inplace

"""
Commands related to subscription:

The 'rover subscribe' command - add a subscription
The 'rover unsubscribe' command - remove a subscription
The 'rover list-subscriptions' command - display information about subscriptions
"""


SUBSCRIBEFILE = 'rover_subscribe'


class Subscriber(SqliteSupport):
    """
### Subscribe

    rover subscribe file

    rover subscribe [net=N] [sta=S] [loc=L] [cha=C] [start [end]]

    rover subscribe N_S_L_C [start [end]]

Subscribe generates a background service, daemon, that regularly compares data
available at the configured server with the local repository. If there is a
discrepancy, available data is downloaded, ingested and indexed. ROVER subscribe
is similar to `rover retrieve` but uses a daemon to regularly update a local
repository.

##### Significant Options

@availability-url
@dataselect-url
@force-request
@verbosity
@log-dir
@log-verbosity
@temp-dir

Most of the download process is controlled by the options provided when starting the service (see
`rover start`).

##### Examples

    rover subscribe N_S_L_C.txt

will instruct the daemon to regularly download, ingest, and index any data missing from the repository for
NSLCs / timespans in the given file.

    rover subscribe IU_ANMO_00_BH1 2017-01-01 2017-01-04

will instruct the daemon to regularly download, ingest and index and data for IU.ANMO.00.BH1 between the given
dates that are missing from the repository.

    """

    def __init__(self, config):
        super().__init__(config)
        self._force_request = config.arg(FORCEREQUEST)
        self._subscriptions_dir = config.dir(SUBSCRIPTIONSDIR)
        self._availability_url = config.arg(AVAILABILITYURL)
        self._dataselect_url = config.arg(DATASELECTURL)
        self._temp_dir = config.dir(TEMPDIR)
        self._create_table()

    def _create_table(self):
        self.execute('''CREATE TABLE IF NOT EXISTS rover_subscriptions (
                           id integer primary key autoincrement,
                           file text unique,
                           availability_url text not null,
                           dataselect_url text not null,
                           creation_epoch int default (cast(strftime('%s', 'now') as int)),
                           last_check_epoch int default NULL,
                           last_error_count int default 0,
                           consistent int default 0
        )''')

    def _check_all_for_overlap(self, path1):
        rows = self.fetchall('''SELECT file FROM rover_subscriptions''')
        for row in rows:
            try:
                RequestComparison(path1, row[0]).assert_no_overlap()
            except Exception as e:
                self._log.error('To avoid duplicating data, subscriptions for the same N_S_L_C and '+
                                'time range are not allowed.')
                self._log.error('Your latest subscription appears to overlap an existing subscription ' +
                                '(see error below).')
                self._log.error('The first 10 lines of your new subscription are:')
                log_file_contents(path1, self._log, 10)
                self._log.error('The first 10 lines of the existing subscription are:')
                log_file_contents(row[0], self._log, 10)
                raise

    def run(self, args):
        # input is a temp file as we prepend options
        try:
            path = unique_path(self._subscriptions_dir, SUBSCRIBEFILE, args[0])
            if len(args) == 1:
                copyfile(args[0], path)
            else:
                build_file(self._log, path, args)
            fix_file_inplace(self._log, path, self._temp_dir)
        except:
            raise Exception('Usage: rover %s (file | [net=N] [sta=S] [cha=C] [loc=L] [start [end]] | N_S_L_C [start [end]])' % SUBSCRIBE)
        if self._force_request:
            self._log.warn('Not checking for overlaps (%s) - may result in duplicate data in the repository' % (mm(FORCEREQUEST)))
        else:
            self._check_all_for_overlap(path)
        self.execute('''INSERT INTO rover_subscriptions (file, availability_url, dataselect_url) VALUES (?, ?, ?)''',
                     (path, self._availability_url, self._dataselect_url))
        self._log.default('Subscribed')


def parse_integers(args):
    # return a list rather than a generator so we fail fast
    ids = []
    for arg in args:
        if ':' in arg:
            try:
                id1, id2 = map(int, arg.split(':'))
            except:
                raise Exception('Cannot parse %s as a pair of IDs' % arg)
        else:
            try:
                id = int(arg)
                id1, id2 = id, id
            except:
                raise Exception('Cannot parse %s as an IDs' % arg)
        ids.append((id1, id2))
    return ids


class SubscriptionLister(SqliteSupport):
    """
### List Subscribe

    rover list-subscribe

    rover list-subscribe N[:M]+

The first form, with no arguments, lists the current subscriptions (these can be removed with `rover unsubscribe`).

The second form, similar to `rover list-retrieve`, shows the data that will be downloaded for that subscription.
The arguments can be single numbers (identifying the subscriptions, as displayed by `rover list-subscrive`), or
ranges (N:M).

The data to be downloaded is not exact, because the daemon may already be downloading data, or because when
the subscription is processed (in the future) the available data have changed.

##### Significant Options

@data-dir
@verbosity
@log-dir
@log-verbosity

##### Examples

    rover list-subscribe

will list the subscriptions and the IDs.

    rover list-subscribe ID

will show what data would be downloaded by the daemon if the subscription were processed immediately.

    """

    def __init__(self, config):
        super().__init__(config)
        self._config = config
        self._dev = config.arg(DEV)

    def run(self, args):
        try:
            ids = parse_integers(args)
        except:
            raise Exception('Usage: rover %s [id | id1:id2] ...' % LIST_SUBSCRIBE)
        if not ids:
            self._list_subscriptions()
        else:
            self._list_downloads(ids)

    def _list_downloads(self, ids):
        download_manager = DownloadManager(self._config)
        for (id1, id2) in ids:
            for id in range(id1, id2+1):
                try:
                    path, availability_url, dataselect_url = self.fetchone(
                        '''SELECT file, availability_url, dataselect_url FROM rover_subscriptions WHERE id = ?''', (id,),
                    quiet=True)
                    self.add = download_manager.add(id, path, False, availability_url, dataselect_url, None)
                except (NoResult, OperationalError):
                    self._log.warn('No subscription %d' % id)
        download_manager.display()

    def _list_subscriptions(self):
        print()
        count = [0]

        def callback(row):
            id, file, availability_url, dataselect_url, creation_epoch, last_check_epoch = row
            date = format_day_epoch(creation_epoch)
            try:
                check = format_time_epoch(last_check_epoch)
            except TypeError:
                check = 'never'
            print('  %d created %s  checked %s' % (id, date, check))
            print('    %s' % file)
            print('    %s' % availability_url)
            print('    %s' % dataselect_url)
            print()
            count[0] += 1

        try:

            self.foreachrow('''SELECT id, file, availability_url, dataselect_url, creation_epoch, last_check_epoch
                                 FROM rover_subscriptions ORDER BY creation_epoch
                            ''', tuple(), callback, quiet=True)
        except OperationalError:
            # no table
            if self._dev: raise

        print("  %d subscription%s" % (count[0], '' if count[0] == 1 else 's'))
        print()


class Unsubscriber(SqliteSupport):
    """
### Unsubscribe

    rover unsubscribe N[:M]+

Deletes one or more subscriptions identified by their indices.
ROVER list-subscribe displays subscription indices. Unsubscribe accepts
integers or ranges of integers (N:M) as arguments. Data associated with a
subscription(s) are not deleted.

To avoid conflicts with subscriptions that are currently being processed,
`rover stop` must stop the daemon before using the unsubscribe command.

##### Significant Options

@data-dir
@verbosity
@log-dir
@log-verbosity

##### Examples

    rover unsubscribe 1:3

will delete subscriptions 1, 2 and 3.

    """

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        if not args:
            raise Exception('Usage: rover %s (id|id1:id2)+' % UNSUBSCRIBE)
        for id1, id2 in parse_integers(args):

            def callback(row):
                file = row[0]
                self._log.debug('Deleting %s' % file)
                safe_unlink(file)

            self.foreachrow('''SELECT file FROM rover_subscriptions WHERE id >= ? AND id <= ?''', (id1, id2), callback)
            self.execute('''DELETE FROM rover_subscriptions WHERE id >= ? AND id <= ?''', (id1, id2))
            self._log.default('Cleared subscriptions between %d and %d' % (id1, id2))


class Trigger(SqliteSupport):
    """
### Trigger

    rover trigger N[:M]+

Ask the daemon to immediately re-process a subscription(s) based on its index.
List-subscribe displays subscriptions indices. Trigger accepts integers or
ranges of integers (N:M) as arguments.

#### Significant Options

@data-dir
@verbosity
@log-dir
@log-verbosity

##### Examples

    rover trigger 2

will ask the daemon to re-process subscription 2.

    """

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        if not args:
            raise Exception('Usage: rover %s (id|id1:id2)+' % TRIGGER)
        for id1, id2 in parse_integers(args):
            self.execute('''UPDATE rover_subscriptions SET last_check_epoch = NULL WHERE id >= ? AND id <= ?''',
                         (id1, id2))
            self._log.default('Cleared last check date for subscriptions between %d and %d' % (id1, id2))
