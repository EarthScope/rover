
from os.path import join
from tempfile import TemporaryDirectory

from rover.ingest import Ingester
from .test_utils import find_root, assert_files, TestConfig


def test_no_compact():
    with TemporaryDirectory() as dir:
        root = find_root()
        config = TestConfig(dir, compact=False)
        ingester = Ingester(config)
        ingester.run((join(root, 'tests', 'data'),))
        n = config.db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 36, n


def test_compact():
    with TemporaryDirectory() as dir:
        root = find_root()
        config = TestConfig(dir)
        ingester = Ingester(config)
        ingester.run((join(root, 'tests', 'data'),))
        n = config.db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 9, n
