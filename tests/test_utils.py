from os import listdir
from os.path import dirname, join
from sqlite3 import connect
from tempfile import mktemp

import rover
from rover import init_log
from rover.index import Indexer
from rover.ingest import MseedindexIngester


def find_root():
    return dirname(dirname(rover.__file__))

def open_db(dbpath):
    db = connect(dbpath)
    c = db.cursor()
    c.execute('PRAGMA foreign_keys = ON')
    return db


def assert_files(dir, *files):
    found = listdir(dir)
    assert len(files) == len(found), 'Found %d files in %s (not %d)' % (len(found), dir, len(files))
    for file in files:
        assert file in found, 'No %s in %s' % (file, found)


def ingest_and_index(dir, data):
    root = find_root()
    log = init_log(dir, 7, 1, 5, 0, 'test')
    dbpath = mktemp(dir=dir)
    mseedindex = join(root, '..', 'mseedindex', 'mseedindex')
    ingester = MseedindexIngester(mseedindex, dbpath, dir, False, None, None, None, log)
    ingester.ingest(data)
    indexer = Indexer(mseedindex, dbpath, dir, 10, False, None, None, None, log)
    indexer.index()
    return log, dbpath


