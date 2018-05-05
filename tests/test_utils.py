
from fnmatch import fnmatch
from os import listdir
from os.path import dirname, join
from tempfile import mktemp

import rover
from rover.logs import init_log
from rover.sqlite import init_db
from rover.index import Indexer
from rover.ingest import MseedindexIngester


def find_root():
    return dirname(dirname(rover.__file__))


def assert_files(dir, *files):
    found = listdir(dir)
    assert len(files) == len(found), 'Found %d files in %s (not %d)' % (len(found), dir, len(files))
    for file in found:
        ok = False
        for glob in files:
            if fnmatch(file, glob):
                ok = True
        if not ok:
            raise Exception('Unexpected file: "%s"', file)


def ingest_and_index(dir, data):
    root = find_root()
    log = init_log(dir, 7, 1, 5, 0, 'test', False, 0)
    dbpath = mktemp(dir=dir)
    db = init_db(dbpath, log)
    mseedindex = join(root, '..', 'mseedindex', 'mseedindex')
    ingester = MseedindexIngester(db, mseedindex, dbpath, dir, False, None, None, None, log)
    ingester.ingest(data)
    indexer = Indexer(db, mseedindex, dbpath, dir, 10, False, None, None, None, False, log)
    indexer.index()
    return log, db, dbpath


