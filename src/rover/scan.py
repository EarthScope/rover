
from genericpath import isdir
from os import listdir, makedirs
from os.path import split, join, isfile, exists, getmtime
from sqlite3 import OperationalError

from .args import DATADIR, ALL, RECURSE
from .sqlite import SqliteSupport
from .utils import canonify, PushBackIterator, in_memory, parse_epoch

"""
Iterators over files on the file system, or in the database, and - building
on that - an iterator over modified files.
"""


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
        self._data_dir = config.dir(DATADIR)
        self._stem = 0
        self._prev_path = None
        self._cursor = self._db.cursor()
        # prev_path and ordering filemodtime desc guarantee that we get the latest
        # modification time if there's more than one value (not clear if mseedindex
        # updates all rows with the latest value).
        try:
            sql = 'SELECT distinct filemodtime, filename FROM tsindex ORDER BY filename ASC, filemodtime DESC'
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
                    self._stem = find_stem(path, self._data_dir, self._log)
                if self._prev_path != path:
                    self._prev_path = path
                return lastmod, join(self._data_dir, path[self._stem + 1:])
            else:
                raise StopIteration()
        except:
            if self._cursor:
                self._cursor.close()
            raise


def RepositoryIterator(root, depth=1):
    """
    Ordered iterator over the filesystem, returning only files from
    the fourth directory level, corresponding to the data files in
    the repository.
    """
    root = canonify(root)
    files = sorted(listdir(root))
    for file in files:
        path = join(root, file)
        if isdir(path) and depth < 4:
            # cannot use 'yield from' as 3to2 doesn't translate it
            for path in RepositoryIterator(path, depth=depth + 1):
                yield path
        elif depth == 4:
            yield path


class ModifiedScanner(SqliteSupport):
    """
    Compare the filesystem and the database (using the iterators above)
    and when there is a discrepancy either remove a database entry or process
    (via subclass) the file.
    """

    def __init__(self, config):
        super().__init__(config)
        self._data_dir = config.dir(DATADIR)
        self._all = config.arg(ALL)
        self._log = config.log
        self._config = config

    def scan_data_dir(self):
        if not exists(self._data_dir):
            makedirs(self._data_dir)
        # pull into memory here to avoid open database when processing
        dbpaths = PushBackIterator(in_memory(DatabasePathIterator(self._config)))
        fspaths = RepositoryIterator(self._data_dir)
        while True:
            closed, dblastmod, dbpath, fspath = False, 0, None, None
            try:
                dblastmod, dbpath = next(dbpaths)
            except StopIteration:
                closed = True
            try:
                fspath = next(fspaths)
            except StopIteration:
                if closed:
                    self.done()
                    return
            # extra entry in file system, so push current database value back,
            # and pretend this entry was in the database, but with a modified date
            # that implies it will be indexed
            if fspath and (not dbpath or fspath < dbpath):
                if not closed:
                    dbpaths.push((dblastmod, dbpath))
                dblastmod, dbpath = '1970-01-01T00:00:00', fspath
            # extra entry in database, needs deleting
            if dbpath and (not fspath or fspath > dbpath):
                self._delete(dbpath)
            # fspath == dbpath so test if need to scan
            else:
                dbepoch = parse_epoch(dblastmod) + 1   # add one because it's rounded down
                if self._all or getmtime(fspath) > dbepoch:
                    self.process(fspath)

    def _delete(self, path):
        self._log.debug('Removing %s from index' % path)
        self.execute('delete from tsindex where filename like ?', (path,))

    def process(self, path):
        raise Exception('Unimplemented')

    def done(self):
        pass


class DirectoryScanner:

    def __init__(self, config):
        self._recurse = config.arg(RECURSE)
        self._log = config.log

    def scan_dirs_and_files(self, paths):

        for path in paths:
            path = canonify(path)
            if not exists(path):
                raise Exception('Cannot find %s' % path)
            if isfile(path):
                self.process(path) # Calls the process method in rover.ingest
            else:
                self._scan_dir(path)
        self.done()

    def _scan_dir(self, dir):
        self._log.debug('Scanning directory %s' % dir)
        for file in listdir(dir):
            path = join(dir, file)
            if isfile(path):
                self.process(path) # Calls the process method in rover.ingest
            elif self._recurse:
                self._scan_dir(path)
            else:
                self._log.warn('Ignoring %s in %s (not a file)' % (file, dir))

    def process(self, path):
        #process method could/should be removed. It does nothing and is confusing for the person reading the code .
        raise Exception('Unimplemented')

    def done(self):
        pass
