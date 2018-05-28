
from enum import Enum
from functools import reduce
from re import sub, compile
from shutil import copyfile
from sqlite3 import OperationalError
import operator

from .download import DownloadManager
from .args import SUBSCRIBE, LIST_SUBSCRIBE, UNSUBSCRIBE, SUBSCRIPTIONSDIR, AVAILABILITYURL, DATASELECTURL, DEV, \
    FORCEREQUEST, mm
from .sqlite import SqliteSupport
from .utils import unique_path, build_file, canonify_dir_and_make, format_day_epoch, safe_unlink, format_time_epoch, \
    sort_file_inplace, parse_short_epoch


"""
Commands related to subscription:

The 'rover subscribe' command - add a subscription
The 'rover unsubscribe' command - remove a subscription 
The 'rover list-subscriptions' command - display information about subscriptions
"""


SUBSCRIBEFILE = 'rover_subscribe'


RegexpHandling = Enum('RegexpHandling', 'IGNORE REMOVE EXPAND')


def parse_request(path, regexpHandling):
    with open(path, 'r') as input:
        for line in input:
            try:
                line = line.strip()
                if line:
                    parts = line.split(' ')
                    sncl = parts[0:4]
                    if regexpHandling == RegexpHandling.EXPAND:
                        if reduce(operator.or_, map(lambda x: '*' in x, sncl)):
                            sncl = list(map(lambda x: sub(r'\*', '\\[A-Za-z0-9\-]*', x), sncl))
                        else:
                            continue  # only yield regexps
                    elif regexpHandling == RegexpHandling.REMOVE:
                        sncl = list(map(lambda x: sub(r'\*', '', x), sncl))
                    elif regexpHandling != RegexpHandling.IGNORE:
                        raise Exception('Bad argument: %s' % regexpHandling)
                    dates = parts[4:]
                    assert len(dates) <= 2
                    yield '_'.join(sncl), dates
            except:
                raise Exception('Cannot parse "%s" in %s (experts can use %s at the risk of duplicating data in the store)' %
                                (line, path, mm(FORCEREQUEST)))


def overlapping_dates(dates1, dates2):
    # if either is open, they must overlap
    if not dates1 or not dates2:
        return True
    # if they're both lower bounds, they must overlap
    if len(dates1) == 1 and len(dates2) == 1:
        return True
    dates1 = list(map(parse_short_epoch, dates1))
    dates2 = list(map(parse_short_epoch, dates2))
    # dates1 is a range
    if len(dates1) == 2:
        # dates2 is a lower bound?
        if len(dates2) == 1:
            # if dates2 starts before dates1 ends, they overlap
            if dates2[0] < dates1[1]:
                return True
        else:
            # easier to find when they don't overlap, and then negate
            # they don't overlap if dates1 ends before dates2 starts, or vice versa
            if not (dates1[1] < dates2[0] or dates2[1] < dates1[0]):
                return True
    # dates1 is a lower bound
    else:
        # if dates1 starts before dates2 ends, they overlap
        if dates1[0] < dates2[1]:
            return True
    # if none of the above, no overlap
    return False


def format_dates(dates):
    dates = list(dates)
    while len(dates) < 2:
        dates.append('open')
    return ' - '.join(dates)


class Regexp:

    def __init__(self, sncls, dates, path):
        self._sncls = sncls
        self._dates = dates
        self._path = path
        self._regexp = compile('(%s)' % '|'.join(sncls))

    def assert_no_overlap(self, sncl, dates, path):
        if self._regexp.match(sncl):
            for i in range(len(self._sncls)):
                if compile(self._sncls[i]).match(sncl) and overlapping_dates(self._dates[i], dates):
                    raise Exception('A pattern in %s matches an entry in %s (%s %s)' %
                                    (self._path, path, sncl, format_dates(dates)))


class SortedRequestComparison:

    def __init__(self, path1, path2):
        self._path1 = path1
        self._path2 = path2

    def _build_regexp(self, path):
        sncls_and_dates = list(parse_request(path, RegexpHandling.EXPAND))
        if sncls_and_dates:
            sncls, dates = list(zip(*sncls_and_dates))
            return Regexp(sncls, dates, path)
        else:
            return None

    def assert_no_overlap(self):
        regexp1 = self._build_regexp(self._path1)
        regexp2 = self._build_regexp(self._path2)
        values1 = parse_request(self._path1, RegexpHandling.REPLACE if regexp1 else RegexpHandling.IGNORE)
        values2 = parse_request(self._path2, RegexpHandling.REPLACE if regexp2 else RegexpHandling.IGNORE)
        try:
            sncl1, dates1 = next(values1)
            sncl2, dates2 = next(values2)
            while True:
                if regexp1:
                    regexp1.assert_no_overlap(sncl2, dates2, self._path2)
                if regexp2:
                    regexp2.assert_no_overlap(sncl1, dates1, self._path1)
                if sncl1 == sncl2 and overlapping_dates(dates1, dates2):
                    raise Exception('Overlap in %s and %s (%s %s and %s %s)' %
                                    (self._path1, self._path2, sncl1, format_dates(dates1), sncl2, format_dates(dates2)))
                if sncl1 < sncl2:
                    sncl1, dates1 = next(values1)
                else:
                    sncl2, dates2 = next(values2)
        except StopIteration:
            return False


class Subscriber(SqliteSupport):
    """
### Subscribe

    rover subscribe

    rover subscribe [net=N] [sta=S] [loc=L] [cha=C] begin [end]

    rover subscribe N_S_L_C begin [end]

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

    rover subscribe IU_ANMO_00_BH1 2017-01-01 2017-01-04

will subscribe to updates from the surrent source (`availability-url` and `dataselect-url` defined in the config)
for the give SNCL between the given dates.
    """

    def __init__(self, config):
        super().__init__(config)
        self._force_request = config.arg(FORCEREQUEST)
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

    def _check_all_for_overlap(self, path1):
        files = self.fetchall('''select file from rover_subscriptions''')
        for path2 in files:
            SortedRequestComparison(path1, path2).assert_no_overlap()

    def run(self, args):
        # input is a temp file as we prepend parameters
        path = unique_path(self._subscriptions_dir, SUBSCRIBEFILE, args[0])
        if len(args) == 1:
            copyfile(args[0], path)
        else:
            try:
                build_file(path, args)
            except:
                raise Exception('Usage: rover %s (file | [net=N] [sta=S] [cha=C] [loc=L] begin [end] | sncl begin [end])' % SUBSCRIBE)
        if self._force_request:
            self._log.warn('Not checking for overlaps (%s) - may result in duplicate data in store' % (mm(FORCEREQUEST)))
        else:
            sort_file_inplace(self._log, path, self._create_table())
            self._check_all_for_overlap(path)
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
