
from sys import version_info

if version_info[0] >= 3:
    from tempfile import TemporaryDirectory
else:
    from backports.tempfile import TemporaryDirectory

from rover.retrieve import Comparer, Retriever
from .test_utils import TestConfig


def test_retrieve():
    with TemporaryDirectory() as dir:
        config = TestConfig(dir, args=['IU.ANMO.00.BH1', '2017-01-01', '2017-01-04'], rover_cmd='python -m rover')
        n_sncls = Comparer(config).run(config.args.args)
        assert n_sncls == 1, n_sncls
        n_downloads = Retriever(config).run(config.args.args)
        assert n_downloads == 3, n_downloads
        n_sncls = Comparer(config).run(config.args.args)
        assert n_sncls == 0, n_sncls
