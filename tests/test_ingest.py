import pytest
from tempfile import TemporaryDirectory
from os.path import join, dirname

from rover.args import DATADIR

from rover.ingest import Ingester
from .shared_utils import assert_files, TestConfig


def test_ingester(tmp_path):
    with TemporaryDirectory() as dir:
        config = TestConfig(dir)
        ingester = Ingester(config)
        ingester.run((join(dirname(__file__), 'data', 'IU.ANMO.00-2010-02-27T06-30-00.000-2010-02-27T10-30-00.000.mseed'),))
        data_dir = config.arg(DATADIR)

        assert_files(data_dir, 'IU')
        assert_files(join(data_dir, 'IU'), '2010')
        assert_files(join(data_dir, 'IU', '2010'), '058')
        assert_files(join(data_dir, 'IU', '2010', '058'), 'ANMO.IU.2010.058')
