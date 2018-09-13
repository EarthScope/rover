
from shutil import copyfile
from sqlite3 import OperationalError

from .request import RequestComparison
from .manager import DownloadManager
from .args import SUBSCRIBE, LIST_SUBSCRIBE, UNSUBSCRIBE, SUBSCRIPTIONSDIR, AVAILABILITYURL, DATASELECTURL, DEV, \
    FORCEREQUEST, mm, TRIGGER, VERBOSITY, NO, DELETEFILES
from .sqlite import SqliteSupport, NoResult
from .utils import unique_path, build_file, format_day_epoch, safe_unlink, format_time_epoch, log_file_contents

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

    rover subscribe [net=N] [sta=S] [loc=L] [cha=C] [begin [end]]

    rover subscribe N_S_L_C [begin [end]]

Arrange for the background service (daemon) to regularly compare available data with the repository then
download, ingest and index any new data.

This is similar to `rover retrieve`, but uses a background service to regularly update the repository.  To
start the service use `rover start`.  See also `rover status` and `rover stop`.

The file argument should contain a list of Net_Sta_Loc_Chans and timespans, as appropriate for calling an Availability
service (eg http://service.iris.edu/irisws/availability/1/).

In the second form above, at least one of `net`, `sta`, `loc`, `cha` should be given (missing values are
taken as wildcards).  For this and the third form a (single-line) file will be automatically constructed
containing that data.

The list of available data is retrieved from the service and compared with the local index.  Data not
available locally are downloaded and ingested.

In the comparison of available data, maximal timespans across all quality and sample rates are used (so quality
and samplerate information is "merged").

A user may have multiple subscriptions (see `rover list-subscribe`), but to avoid downloading duplicate data
they must not describe overlapping data.  To enforce this, requests are checked on submission.

##### Significant Parameters

@availability-url
@dataselect-url
@force-request
@verbosity
@log-dir
@log-verbosity

Most of the download process is controlled by the parameters provided when starting the service (see
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
        self._create_table()

    def _create_table(self):
        self.execute('''create table if not exists rover_subscriptions (
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
        rows = self.fetchall('''select file from rover_subscriptions''')
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
                raise e


    def run(self, args):
        # input is a temp file as we prepend parameters
        try:
            path = unique_path(self._subscriptions_dir, SUBSCRIBEFILE, args[0])
            if len(args) == 1:
                copyfile(args[0], path)
            else:
                build_file(self._log, path, args)
        except:
            raise Exception('Usage: rover %s (file | [net=N] [sta=S] [cha=C] [loc=L] [begin [end]] | N_S_L_C [begin [end]])' % SUBSCRIBE)
        if self._force_request:
            self._log.warn('Not checking for overlaps (%s) - may result in duplicate data in the repository' % (mm(FORCEREQUEST)))
        else:
            self._check_all_for_overlap(path)
        self.execute('''insert into rover_subscriptions (file, availability_url, dataselect_url) values (?, ?, ?)''',
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

##### Significant Parameters

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
                        '''select file, availability_url, dataselect_url from rover_subscriptions where id = ?''', (id,),
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

            self.foreachrow('''select id, file, availability_url, dataselect_url, creation_epoch, last_check_epoch
                                 from rover_subscriptions order by creation_epoch
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

Delete one or more subscriptions.  The arguments can be single numbers (identifying the subscriptions, as
displayed by `rover list-subscrive`), or ranges (N:M).

Note: To avoid conflicts with subscriptions that are currently being processed, the daemon must be stopped
(with `rover stop`) before using the `unsubscribe` command.

##### Significant Parameters

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

            self.foreachrow('''select file from rover_subscriptions where id >= ? and id <= ?''', (id1, id2), callback)
            self.execute('''delete from rover_subscriptions where id >= ? and id <= ?''', (id1, id2))
            self._log.default('Cleared subscriptions between %d and %d' % (id1, id2))


class Trigger(SqliteSupport):
    """
### Trigger

    rover trigger N[:M]+

Ask the daemon to re-process the given subscriptions.  The arguments can be single numbers (identifying the
subscriptions, as displayed by `rover list-subscribe`), or ranges (N:M).

More exactly, this command resets the "last checked" date in the database, so when the daemon re-checks the
database (typically once per minute) it will process the subscription.

#### Significant Parameters

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
            self.execute('''update rover_subscriptions set last_check_epoch = NULL where id >= ? and id <= ?''',
                         (id1, id2))
            self._log.default('Cleared last check date for subscriptions between %d and %d' % (id1, id2))
