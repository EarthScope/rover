
from sys import version_info
from os.path import join

from rover.args import MSEEDDIR

if version_info[0] >= 3:
    from tempfile import TemporaryDirectory
else:
    from backports.tempfile import TemporaryDirectory

from rover.ingest import Ingester
from .test_utils import find_root, assert_files, TestConfig


def test_ingester():
    with TemporaryDirectory() as dir:
        root = find_root()
        config = TestConfig(dir)
        ingester = Ingester(config)
        ingester.run((join(root, 'tests', 'data', 'IU.ANMO.00-2010-02-27T06-30-00.000-2010-02-27T10-30-00.000.mseed'),))
        mseed_dir = config.arg(MSEEDDIR)
        assert_files(mseed_dir, 'IU')
        assert_files(join(mseed_dir, 'IU'), '2010')
        assert_files(join(mseed_dir, 'IU', '2010'), '058')
        assert_files(join(mseed_dir, 'IU', '2010', '058'), 'ANMO.IU.2010.058')
