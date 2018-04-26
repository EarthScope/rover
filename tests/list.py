
from sys import version_info
from tempfile import TemporaryDirectory
from os.path import join

# mess for handling str type in buffer
if version_info >= (3,0):
    from io import StringIO as buffer
else:
    from io import BytesIO as buffer

from rover.list import IndexLister
from test_utils import find_root, ingest_and_index


def run_args(args):
    root = find_root()
    with TemporaryDirectory() as dir:
        log, dbpath = ingest_and_index(dir, (join(root, 'tests', 'data'),))
        stdout = buffer()
        IndexLister(dbpath, log).list(args, stdout=stdout)
        stdout.seek(0)
        return stdout.read()


def assert_bad_args(args, msg):
    try:
        run_args(args)
    except Exception as e:
        assert msg in str(e), str(e)


# this is a bit inefficient - do an import and index for every test

def test_bad_begin():
    assert_bad_args(['begin=2010-1'], 'Poorly formed time "2010-1"')

def test_ambiguous():
    assert_bad_args(['s=foo'], 'Ambiguous parameter: s')

def test_two_flags():
    assert_bad_args(['count', 'join'], 'Cannot specify multiple keys')

def test_count():
    n = run_args(['count'])
    assert int(n) == 9

