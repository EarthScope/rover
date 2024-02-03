import pytest
from tempfile import TemporaryDirectory
from io import StringIO as buffer
from os import unlink
from os.path import join, dirname

from rover import IndexLister
from rover.args import DATADIR

from rover.index import Indexer
from .shared_utils import ingest_and_index


def test_ingest_and_index():
    testdir = join(dirname(__file__), 'data')

    with TemporaryDirectory() as dir:
        config = ingest_and_index(dir, [testdir])
        n = config.db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 36, n


def test_deleted_file():
    testdir = join(dirname(__file__), 'data')

    with TemporaryDirectory() as dir:
        config = ingest_and_index(dir, [testdir])
        unlink(join(config.arg(DATADIR), 'IU', '2010', '058', 'ANMO.IU.2010.058'))
        indexer = Indexer(config)
        indexer.run([])
        n = config.db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 0, n


def run_list_index(dir, args):
    testdir = join(dirname(__file__), 'data')
    config = ingest_and_index(dir, [testdir])
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
    with TemporaryDirectory() as dir:
        assert_bad_args(dir, ['start=2010-1'], 'Cannot parse timestamp "2010-1"')


def test_ambiguous():
    with TemporaryDirectory() as dir:
        assert_bad_args(dir, ['s=foo'], 'Ambiguous parameter: s')


def test_two_flags():
    with TemporaryDirectory() as dir:
        assert_bad_args(dir, ['count', 'join'], 'Cannot specify multiple keys')


def test_count():
    with TemporaryDirectory() as dir:
        n = run_list_index(dir, ['count'])
        assert int(n) == 36, n
