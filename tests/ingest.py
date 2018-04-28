
from tempfile import TemporaryDirectory
from tempfile import mktemp
from os.path import join

from rover import init_log
from rover.ingest import MseedindexIngester
from test_utils import find_root, open_db, assert_files


def test_mseedindexingester():
    root = find_root()
    with TemporaryDirectory() as dir:
        log = init_log(dir, 7, 1, 5, 0, 'test')
        dbpath = mktemp(dir=dir)
        ingester = MseedindexIngester(join(root, '..', 'mseedindex', 'mseedindex'),
                                      dbpath, dir, False, None, None, None, log)
        ingester.ingest((join(root, 'tests', 'data'),))
        assert_files(dir, 'test.log', 'IU', 'tmp*')
        assert_files(join(dir, 'IU'), '2010')
        assert_files(join(dir, 'IU', '2010'), '58')
        assert_files(join(dir, 'IU', '2010', '58'), 'ANMO.IU.2010.58')
