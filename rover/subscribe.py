
from shutil import copyfile
from sqlite3 import OperationalError

from .args import SUBSCRIBE, LIST_SUBSCRIPTIONS, UNSUBSCRIBE
from .sqlite import SqliteSupport
from .utils import unique_path, build_file, canonify_dir_and_make, format_day_epoch, safe_unlink

"""
The 'rover subscribe', 'rover list-subscriptions' and 'rover unsubscribe' commands.
"""


SUBSCRIBEFILE = 'rover_subscribe'


class Subscriber(SqliteSupport):
    """
### Subscribe

    rover subscribe

    rover subscribe N.S.L.C begin [end]
    """

    def __init__(self, config):
        super().__init__(config)
        log, args = config.log, config.args
        self._subscription_dir = canonify_dir_and_make(args.subscription_dir)
        self._availability_url = args.availability_url
        self._dataselect_url = args.dataselect_url
        self._create_table()

    def _create_table(self):
        self.execute('''create table if not exists rover_subscriptions (
                           id integer primary key autoincrement,
                           file text unique,
                           availability_url text not null,
                           dataselect_url text not null,
                           creation_epoch int default (cast(strftime('%s', 'now') as int))
        )''')

    def run(self, args):
        if len(args) == 0 or len(args) > 3:
            raise Exception('Usage: rover %s (file|sncl begin [end])' % SUBSCRIBE)
        else:
            # input is a temp file as we prepend parameters
            path = unique_path(self._subscription_dir, SUBSCRIBEFILE, args[0])
            if len(args) == 1:
                copyfile(args[0], path)
            else:
                build_file(path, *args)
            self.execute('''insert into rover_subscriptions (file, availability_url, dataselect_url) values (?, ?, ?)''',
                         (path, self._availability_url, self._dataselect_url))


class SubscriptionLister(SqliteSupport):
    """
### List Subscriptions

    rover list-subscriptions
    """

    def __init__(self, config):
        super().__init__(config)
        log, args = config.log, config.args
        self._dev = args.dev

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % LIST_SUBSCRIPTIONS)
        print()

        def callback(row):
            id, file, availability_url, dataselect_url, creation_epoch = row
            date = format_day_epoch(creation_epoch)
            print('  %d %s' % (id, file))
            print('    %s' % availability_url)
            print('    %s' % dataselect_url)
            print()

        try:
            self.foreachrow('''select * from rover_subscriptions order by creation_epoch''', tuple(), callback, quiet=True)
        except OperationalError:
            # no table
            if self._dev: raise


class Unsubscriber(SqliteSupport):
    """
### Unsubscribe

    rover unsubscribe (id|id1:id2)+
    """

    def __init__(self, config):
        super().__init__(config)
        log, args = config.log, config.args

    def _parse_args(self, args):
        ids = []
        for arg in args:
            if ':' in arg:
                try:
                    id1, id2 = map(int, arg.split(''))
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

    def run(self, args):
        if not args:
            raise Exception('Usage: rover %s (id|id1:id2)+' % UNSUBSCRIBE)
        ids = self._parse_args(args)
        for id1, id2 in ids:

            def callback(row):
                file = row[0]
                self._log.debug('Deleting %s' % file)
                safe_unlink(file)

            self.foreachrow('''select file from rover_subscriptions where id >= ? and id <= ?''', (id1, id2), callback)
            self.execute('''delete from rover_subscriptions where id >= ? and id <= ?''', (id1, id2))
