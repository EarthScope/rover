
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


def test_check_only():
    with TemporaryDirectory() as dir:
        root = find_root()
        config = TestConfig(dir, compact=True)
        ingester = Ingester(config)
        try:
            ingester.run((join(root, 'tests', 'data'),))
        except Exception as e:
            assert 'Overlapping' in str(e), e
        else:
            assert False, 'Expected exception'


def test_merge():
    with TemporaryDirectory() as dir:
        root = find_root()
        config = TestConfig(dir, compact=True, compact_merge=True)
        ingester = Ingester(config)
        ingester.run((join(root, 'tests', 'data'),))
        n = config.db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 18, n
