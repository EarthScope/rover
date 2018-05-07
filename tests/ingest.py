
from os.path import join
from tempfile import TemporaryDirectory

from rover.ingest import Ingester
from .test_utils import find_root, assert_files, TestConfig


def test_mseedindexingester():
    with TemporaryDirectory() as dir:
        root = find_root()
        config = TestConfig(dir)
        ingester = Ingester(config)
        ingester.run((join(root, 'tests', 'data'),))
        mseed_dir = config.args.mseed_dir
        assert_files(mseed_dir, 'IU')
        assert_files(join(mseed_dir, 'IU'), '2010')
        assert_files(join(mseed_dir, 'IU', '2010'), '58')
        assert_files(join(mseed_dir, 'IU', '2010', '58'), 'ANMO.IU.2010.58')
