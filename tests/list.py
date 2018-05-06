
from sys import version_info
from tempfile import TemporaryDirectory
from os.path import join

# mess for handling str type in buffer
if version_info >= (3,0):
    from io import StringIO as buffer
else:
    from io import BytesIO as buffer

from rover.list import IndexLister
from .test_utils import find_root, ingest_and_index


def run_args(dir, args):
    root = find_root()
    config = ingest_and_index(dir, (join(root, 'tests', 'data'),))
    stdout = buffer()
    IndexLister(config).list(args, stdout=stdout)
    stdout.seek(0)
    return stdout.read()


def assert_bad_args(dir, args, msg):
    try:
        run_args(dir, args)
    except Exception as e:
        assert msg in str(e), str(e)


# this is a bit inefficient - do an import and index for every test

def test_bad_begin():
    with TemporaryDirectory() as dir:
        assert_bad_args(dir, ['begin=2010-1'], 'Poorly formed time "2010-1"')

def test_ambiguous():
    with TemporaryDirectory() as dir:
      assert_bad_args(dir, ['s=foo'], 'Ambiguous parameter: s')

def test_two_flags():
    with TemporaryDirectory() as dir:
      assert_bad_args(dir, ['count', 'join'], 'Cannot specify multiple keys')

def test_count():
    with TemporaryDirectory() as dir:
        n = run_args(dir, ['count'])
        assert int(n) == 9

