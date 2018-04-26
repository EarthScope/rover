
from tempfile import TemporaryDirectory
from tempfile import mktemp
from os.path import join

from rover.index import Indexer
from rover.ingest import MseedindexIngester
from rover import init_log
from test_utils import find_root, open_db


def test_ingest_and_index():
    root = find_root()
    with TemporaryDirectory() as dir:
        log = init_log(dir, 3, 1, 5, 0, 'test')
        dbpath = mktemp()
        mseedindex = join(root, '..', 'mseedindex', 'mseedindex')
        ingester = MseedindexIngester(mseedindex, dbpath, dir, False, None, None, None, log)
        ingester.ingest((join(root, 'tests', 'data'),))
        indexer = Indexer(mseedindex, dbpath, dir, 10, False, None, None, None, log)
        indexer.index()
        db = open_db(dbpath)
        n = db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 9, n
