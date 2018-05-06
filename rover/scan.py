
from datetime import datetime
from genericpath import isdir
from os import listdir
from os.path import split, join
from sqlite3 import OperationalError

from .utils import PushBackIterator
from .sqlite import SqliteSupport
from .utils import canonify, parse_short_time, lastmod
from .workers import Workers


EPOCH = datetime.utcfromtimestamp(0)


def find_stem(path, root, log):
    """
    Find the initial part of path that matches root (and return the length).

    This is needed because we don't know that filenames in the mseedindex table
    are canonified in the same way as here.  So links, etc may make things look
    different even though they are equivalent.
    """
    original_path = path
    while True:
        if canonify(path) == root:
            log.debug('Matched %s as %s' % (root, path))
            return len(path)
        path, _ = split(path)
        if not path:
            raise Exception('Could not find canonical prefix to %s' % original_path)


class DatabasePathIterator(SqliteSupport):
    """
    Ordered iterator over files known in the database.
    We also return last modified as that is used in the indexer.

    The aim here is to be as efficient as possible.  So rather than iterating
    over the filesystem (only) and querying the database for each file, we
    do a single scan of the database and use that to provide a list of known
    files.
    """

    def __init__(self, config):
        super().__init__(config)
        self._mseed_dir = canonify(config.args.mseed_dir)
        self._stem = 0
        self._prev_path = None
        self._cursor = self._db.cursor()
        # prev_path and ordering filemodtime desc guarantee that we get the latest
        # modification time if there's more than one value (not clear if mseedindex
        # updates all rows with the latest value).
        try:
            sql = 'select distinct filemodtime, filename from tsindex order by filename asc, filemodtime desc'
            self._log.debug('Execute: %s' % sql)
            self._cursor.execute(sql)
        except OperationalError as e:
            # this is the case when there's no table yet, so no files
            self._cursor = None

    def __iter__(self):
        return self

    def __next__(self):
        try:
            if self._cursor:
                lastmod, path = next(self._cursor)
                if not self._prev_path:
                    self._stem = find_stem(path, self._mseed_dir, self._log)
                if self._prev_path != path:
                    self._prev_path = path
                return lastmod, join(self._mseed_dir, path[self._stem + 1:])
            else:
                raise StopIteration()
        except:
            if self._cursor:
                self._cursor.close()
            raise


def fileSystemPathIterator(root, depth=1):
    """
    Ordered iterator over the filesystem, returning only files from
    the fourth directory level, corresponding to the data files in
    the store.
    """
    root = canonify(root)
    files = sorted(listdir(root))
    for file in files:
        path = join(root, file)
        if isdir(path) and depth < 4:
            # cannot use 'yield from' as 3to2 doesn't translate it
            for path in fileSystemPathIterator(path, depth=depth+1):
                yield path
        elif depth == 4:
            yield path


class MseedFileScanner(SqliteSupport):
    """
    Compare the filesystem and the database (using the iterators above)
    and when there is a discrepancy either add or remove an entry.
    """

    def __init__(self, config):
        super().__init__(config)
        args, log = config.args, config.log
        self._mseed_dir = args.mseed_dir
        self._workers = Workers(config, args.mseed_workers)
        self._log = log
        self._config = config

    def run(self):
        dbpaths = PushBackIterator(DatabasePathIterator(self._config))
        fspaths = fileSystemPathIterator(self._mseed_dir)
        while True:
            # default values for paths work with ordering
            closed, dblastmod, dbpath, fspath = False, 0, ' ', ' '
            try:
                dblastmod, dbpath = next(dbpaths)
            except StopIteration:
                closed = True
            try:
                fspath = next(fspaths)
            except StopIteration:
                if closed:
                    self._workers.wait_for_all()
                    return
            # extra entry in file system, so push current database value back,
            # and pretend this entry was in the database, but with a modified date
            # that implies it will be indexed
            if fspath > dbpath:
                if not closed:
                    dbpaths.push((dblastmod, dbpath))
                dblastmod, dbpath = '1970-01-01T00:00:00', fspath
            # extra entry in database, needs deleting
            if fspath < dbpath:
                self._delete(dbpath)
            # fspath == dbpath so test if need to scan
            else:
                dbepoch = (parse_short_time(dblastmod) - EPOCH).total_seconds() + 1   # add one because it's rounded down
                if lastmod(fspath) > dbepoch:
                    self._process(fspath)

    def _delete(self, path):
        self._log.debug('Removing %s from index' % path)
        self._execute('delete from tsindex where filename like ?', (path,))

    def _process(self, path):
        raise Exception('Unimplemented')

