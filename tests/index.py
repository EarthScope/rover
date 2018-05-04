
from os.path import join
from tempfile import TemporaryDirectory
from os import unlink, rmdir

from rover.index import Indexer
from .test_utils import find_root, ingest_and_index


def test_ingest_and_index():
    root = find_root()
    with TemporaryDirectory() as dir:
        log, db, dbpath = ingest_and_index(dir, (join(root, 'tests', 'data'),))
        n = db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 9, n


def test_deleted_file():
    root = find_root()
    with TemporaryDirectory() as dir:
        log, db, dbpath = ingest_and_index(dir, (join(root, 'tests', 'data'),))
        unlink(join(dir, 'IU', '2010', '58', 'ANMO.IU.2010.58'))
        root = find_root()
        mseedindex = join(root, '..', 'mseedindex', 'mseedindex')
        indexer = Indexer(db, mseedindex, dbpath, dir, 10, False, None, None, None, False, log)
        indexer.index()
        n = db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 0, n
