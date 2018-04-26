from os import listdir
from os.path import dirname
from sqlite3 import connect

import rover


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
