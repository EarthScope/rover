
from os.path import join
from tempfile import TemporaryDirectory

from test_utils import find_root, open_db, ingest_and_index


def test_ingest_and_index():
    root = find_root()
    with TemporaryDirectory() as dir:
        log, dbpath = ingest_and_index(dir, (join(root, 'tests', 'data'),))
        db = open_db(dbpath)
        n = db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 9, n
