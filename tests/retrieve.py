

from os.path import join
from tempfile import TemporaryDirectory

from rover.retrieve import retrieve
from .test_utils import assert_files, TestConfig


def test_retrieve():
    with TemporaryDirectory() as dir:
        config = TestConfig(dir, args=['IU.ANMO.00.BH1', '2017-01-01', '2017-01-04'], rover_cmd='python -m rover')
        n_sncls = retrieve(config, False)
        assert n_sncls == 1, n_sncls
        n_downloads = retrieve(config, True)
        assert n_downloads == 3, n_downloads
        n_sncls = retrieve(config, False)
        assert n_sncls == 0, n_sncls
