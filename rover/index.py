
from os import listdir, stat, makedirs
from os.path import join, basename, isfile, isdir, dirname, exists, split
from sqlite3 import OperationalError
from subprocess import Popen
from time import sleep

from .utils import canonify, check_cmd, check_leap
from .sqlite import SqliteSupport, NoResult


class Workers:
    """
    A collection of processes that run asynchronously.  Note that the Python
    code here does NOT run asynchonously - it will block if there are no free
    workers.

    The idea is that we run N meedindex processes in the background so that
    we are not waiting on them to complete.
    """

    def __init__(self, size, log):
        self._log = log
        self._size = size
        self._workers = []  # (command, popen)

    def execute(self, command):
        """
        Execute the command in a separate process.
        """
        self._wait_for_space()
        self._log.debug('Adding worker for "%s"' % command)
        self._workers.append((command, Popen(command, shell=True)))

    def _wait_for_space(self):
        while True:
            self._check()
            if len(self._workers) < self._size:
                self._log.debug('Space for new worker')
                return
            sleep(0.1)

    def _check(self):
        i = len(self._workers) - 1
        while i > -1:
            cmd, process = self._workers[i]
            process.poll()
            if process.returncode is not None:
                if process.returncode:
                    raise Exception('"%s" returned %d' % (cmd, process.returncode))
                else:
                    self._log.debug('"%s" succeeded' % (cmd,))
                self._workers = self._workers[:i] + self._workers[i+1:]
            i -= 1

    def wait_for_all(self):
        """
        Wait for all remaining processes to finish.
        """
        while True:
            self._check()
            if not self._workers:
                self._log.debug('No workers remain')
                return
            sleep(0.1)



def find_stem(path, root, log):
    """
    Find the initial part of path that matches rot (and return the length).

    This is needed because we don't know that filenames in the mseedindex table
    are anonified in the same way as here.  So links, etc may make things look
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
            self._log.debug(e)
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
    Ordered iteratoin over the filesystem, returning only files from
    the fourth directory level, corresponding to the data files in
    the store.
    """
    root = canonify(root)
    files = sorted(listdir(root))
    for file in files:
        path = join(root, file)
        if isdir(path):
            # cannot use yield from as 3to2 doesn't translate it
            for path in fileSystemPathIterator(path, depth=depth+1):
                yield path
        elif depth == 4:
            yield path


class PushBackIterator:
    """
    Modify an iterator so that a (single) value can be pushed back
    and will be returned next iteration.
    """

    def __init__(self, iter):
        self._iter = iter
        self._pushed = None

    def push(self, value):
        if self._pushed:
            raise Exception('Cannot push multiple values')
        self._pushed = value

    def __iter__(self):
        return self

    def __next__(self):
        if self._pushed:
            value = self._pushed
            self._pushed = None
        else:
            value = next(self._iter)
        return value


class Indexer(SqliteSupport):
    """
    Compare the filesystem and the database (using the iterators above)
    and when there is a discrepancy either add or remove an entry.
    """

    def __init__(self, mseedindex, dbpath, root, n_workers, leap, leap_expire, leap_file, leap_url, log):
        super().__init__(dbpath, log)
        self._dbpaths = PushBackIterator(DatabasePathIterator(dbpath, root, log))
        self._fspaths = fileSystemPathIterator(root)
        self._mseedindex = mseedindex
        self._workers = Workers(n_workers, log)
        self._leap_file = check_leap(leap, leap_expire, leap_file, leap_url, log)
        self._log = log

    def index(self):
        while True:
            closed, lastmod, dbpath, fspath = False, 0, ' ', ' '
            try:
                lastmod, dbpath = next(self._dbpaths)
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
                    self._dbpaths.push((lastmod, dbpath))
                lastmod, dbpath = 0, fspath
            # extra entry in database, needs deleting
            if fspath < dbpath:
                self._delete(dbpath)
            # fpath == dbpath so test if need to scan
            else:
                statinfo = stat(fspath)
                if statinfo.st_atime != lastmod:
                    self._index(fspath)

    def _delete(self, path):
        self._log.debug('Removing %s from index' % path)
        self._execute('delete from tsindex where filename like ?', (path,))

    def _index(self, path):
        self._log.debug('Sanning %s' % path)
        self._workers.execute('LIBMSEED_LEAPSECOND_FILE=%s %s -sqlite %s %s'
                              % (self._leap_file, self._mseedindex, self._dbpath, path))


def index(args, log):
    """
    Implement the index command.
    """
    indexer = Indexer(args.mseed_cmd, args.mseed_db, args.mseed_dir, args.mseed_workers,
                      args.leap, args.leap_expire, args.leap_file, args.leap_url, log)
    indexer.index()
