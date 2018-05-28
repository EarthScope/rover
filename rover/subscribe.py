
from shutil import copyfile
from sqlite3 import OperationalError

from .download import DownloadManager
from .args import SUBSCRIBE, LIST_SUBSCRIBE, UNSUBSCRIBE, SUBSCRIPTIONSDIR, AVAILABILITYURL, DATASELECTURL, DEV
from .sqlite import SqliteSupport
from .utils import unique_path, build_file, canonify_dir_and_make, format_day_epoch, safe_unlink, format_time_epoch

"""
The 'rover subscribe', 'rover list-subscriptions' and 'rover unsubscribe' commands.
"""


SUBSCRIBEFILE = 'rover_subscribe'


class Subscriber(SqliteSupport):
    """
### Subscribe

    rover subscribe

    rover subscribe N.S.L.C begin [end]

##### Significant Parameters

@subscriptions-dir
@availability-url
@dataselect-url
@mseed-db
@verbosity
@log-dir
@log-name
@log-verbosity

##### Examples

    rover subscribe IU.ANMO.00.BH1 2017-01-01 2017-01-04

will subscribe to updates from the surrent source (`availability-url` and `dataselect-url` defined in the config)
for the give SNCL between the given dates.
    """

    def __init__(self, config):
        super().__init__(config)
        self._subscriptions_dir = config.dir_path(SUBSCRIPTIONSDIR)
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
                           last_check_epoch int default NULL
        )''')

    def run(self, args):
        if len(args) == 0 or len(args) > 3:
            raise Exception('Usage: rover %s (file|sncl begin [end])' % SUBSCRIBE)
        else:
            # input is a temp file as we prepend parameters
            path = unique_path(self._subscriptions_dir, SUBSCRIBEFILE, args[0])
            if len(args) == 1:
                copyfile(args[0], path)
            else:
                build_file(path, args)
            self.execute('''insert into rover_subscriptions (file, availability_url, dataselect_url) values (?, ?, ?)''',
                         (path, self._availability_url, self._dataselect_url))


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
### List Subscriptions

    rover list-subscriptions

##### Significant Parameters

@mseed-db
@verbosity
@log-dir
@log-name
@log-verbosity

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
                path, availability_url, dataselect_url = self.fetchone(
                    '''select file, availability_url, dataselect_url from rover_subscriptions where id = ?''', (id,))
                download_manager.add(id, path, availability_url, dataselect_url)
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

    rover unsubscribe (id|id1:id2)+

##### Significant Parameters

@mseed-db
@verbosity
@log-dir
@log-name
@log-verbosity

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
