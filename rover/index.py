
from os import listdir
from os.path import join, isdir, split
from sqlite3 import OperationalError

from .workers import Workers
from .sqlite import SqliteSupport
from .utils import canonify, check_leap, lastmod, PushBackIterator


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

    def __init__(self, dbpath, root, log):
        super().__init__(dbpath, log)
        self._root = canonify(root)
        self._stem = 0
        self._prev_path = None
        self._cursor = self._db.cursor()
        # prev_path and ordering filemodtime desc guarantee that we get the latest
        # modification time if there's more than one value (not clear if mseedindex
        # updates all rows with the latest value).
        try:
            self._cursor.execute('select distinct filemodtime, filename from tsindex order by filename asc, filemodtime desc')
        except OperationalError as e:
            # this is the case when there's no table yet, so no files
            self._cursor = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._cursor:
            lastmod, path = next(self._cursor)
            if not self._prev_path:
                self._stem = find_stem(path, self._root, self._log)
            if self._prev_path != path:
                self._prev_path = path
            return lastmod, join(self._root, path[self._stem+1:])
        else:
            raise StopIteration()


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


class Indexer(SqliteSupport):
    """
    Compare the filesystem and the database (using the iterators above)
    and when there is a discrepancy either add or remove an entry.
    """

    def __init__(self, db, mseedindex, mseed_db, root, n_workers, leap, leap_expire, leap_file, leap_url, dev, log):
        super().__init__(db, log)
        self._dbpaths = PushBackIterator(DatabasePathIterator(db, root, log))
        self._fspaths = fileSystemPathIterator(root)
        self._mseedindex = mseedindex
        self._mseed_db = mseed_db
        self._workers = Workers(n_workers, log)
        self._leap_file = check_leap(leap, leap_expire, leap_file, leap_url, log)
        self._dev = dev
        self._log = log

    def index(self):
        while True:
            # default values for paths work with ordering
            closed, dblastmod, dbpath, fspath = False, 0, ' ', ' '
            try:
                dblastmod, dbpath = next(self._dbpaths)
            except StopIteration:
                closed = True
            try:
                fspath = next(self._fspaths)
            except StopIteration:
                if closed:
                    self._workers.wait_for_all()
                    return
            # extra entry in file system, so push current database value back,
            # and pretend this entry was in the database, but with a modified date
            # that implies it will be indexed
            if fspath > dbpath:
                if not closed:
                    self._dbpaths.push((dblastmod, dbpath))
                dblastmod, dbpath = 0, fspath
            # extra entry in database, needs deleting
            if fspath < dbpath:
                self._delete(dbpath)
            # fspath == dbpath so test if need to scan
            else:
                if lastmod(fspath) != dblastmod:
                    self._index(fspath)

    def _delete(self, path):
        self._log.debug('Removing %s from index' % path)
        self._execute('delete from tsindex where filename like ?', (path,))

    def _index(self, path):
        self._log.debug('Scanning %s' % path)
        # todo - windows var
        self._workers.execute('LIBMSEED_LEAPSECOND_FILE=%s %s %s -sqlite %s %s'
                              % (self._leap_file, self._mseedindex, '-v -v' if self._dev else '', self._mseed_db, path))


def index(core):
    """
    Implement the index command.
    """
    indexer = Indexer(core.db, core.args.mseed_cmd, core.args.mseed_db, core.args.mseed_dir, core.args.mseed_workers,
                      core.args.leap, core.args.leap_expire, core.args.leap_file, core.args.leap_url, core.args.dev,
                      core.log)
    indexer.index()
