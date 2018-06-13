
from sys import version_info
if version_info[0] >= 3:
    from io import StringIO as buffer
else:
    from io import BytesIO as buffer
from os import unlink
from os.path import join

from rover import IndexLister
from rover.args import MSEEDDIR

if version_info[0] >= 3:
    from tempfile import TemporaryDirectory
else:
    from backports.tempfile import TemporaryDirectory

from rover.index import Indexer
from .test_utils import find_root, ingest_and_index, WindowsTemp


def test_ingest_and_index():
    root = find_root()
    with WindowsTemp(TemporaryDirectory) as dir:
        config = ingest_and_index(dir, (join(root, 'tests', 'data'),))
        n = config.db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 36, n


def test_deleted_file():
    root = find_root()
    with WindowsTemp(TemporaryDirectory) as dir:
        config = ingest_and_index(dir, (join(root, 'tests', 'data'),))
        unlink(join(config.arg(MSEEDDIR), 'IU', '2010', '058', 'ANMO.IU.2010.058'))
        indexer = Indexer(config)
        indexer.run([])
        n = config.db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 0, n


def run_list_index(dir, args):
    root = find_root()
    config = ingest_and_index(dir, (join(root, 'tests', 'data'),))
    stdout = buffer()
    IndexLister(config).run(args, stdout=stdout)
    stdout.seek(0)
    return stdout.read()


def assert_bad_args(dir, args, msg):
    try:
        run_list_index(dir, args)
    except Exception as e:
        assert msg in str(e), str(e)


def test_bad_begin():
    with WindowsTemp(TemporaryDirectory) as dir:
        assert_bad_args(dir, ['begin=2010-1'], 'Poorly formed time "2010-1"')


def test_ambiguous():
    with WindowsTemp(TemporaryDirectory) as dir:
        assert_bad_args(dir, ['s=foo'], 'Ambiguous parameter: s')


def test_two_flags():
    with WindowsTemp(TemporaryDirectory) as dir:
        assert_bad_args(dir, ['count', 'join'], 'Cannot specify multiple keys')


def test_count():
    with WindowsTemp(TemporaryDirectory) as dir:
        n = run_list_index(dir, ['count'])
        assert int(n) == 36, n
