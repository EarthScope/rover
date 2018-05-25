
from sys import version_info
from os import unlink
from os.path import join

from rover.args import MSEEDDIR

if version_info[0] >= 3:
    from tempfile import TemporaryDirectory
else:
    from backports.tempfile import TemporaryDirectory

from rover.index import Indexer
from .test_utils import find_root, ingest_and_index


def test_ingest_and_index():
    root = find_root()
    with TemporaryDirectory() as dir:
        config = ingest_and_index(dir, (join(root, 'tests', 'data'),))
        n = config.db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 36, n


def test_deleted_file():
    root = find_root()
    with TemporaryDirectory() as dir:
        config = ingest_and_index(dir, (join(root, 'tests', 'data'),))
        unlink(join(config.arg(MSEEDDIR), 'IU', '2010', '058', 'ANMO.IU.2010.058'))
        indexer = Indexer(config)
        indexer.run([])
        n = config.db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 0, n
