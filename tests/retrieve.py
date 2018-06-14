
from sys import version_info

from rover import ProcessManager

if version_info[0] >= 3:
    from tempfile import TemporaryDirectory
else:
    from backports.tempfile import TemporaryDirectory

from rover.retrieve import ListRetriever, Retriever
from .test_utils import TestConfig, WindowsTemp


def test_retrieve():
    with WindowsTemp(TemporaryDirectory, False) as dir:
        config = TestConfig(dir, args=['IU_ANMO_00_BH1', '2017-01-01', '2017-01-04'], command='retrieve',
                            rover_cmd='python -m rover', verbosity=0, delete_files=False, dev=True, log_verbosity=5)
        n_sncls = ListRetriever(config).run(config.args)
        assert n_sncls == 1, n_sncls
        with ProcessManager(config):
            n_downloads = Retriever(config).run(config.args)
        assert n_downloads == 3, n_downloads
        n_sncls = ListRetriever(config).run(config.args)
        assert n_sncls == 0, n_sncls
        # alternate syntax
        config = TestConfig(dir, args=['net=IU', 'sta=ANMO', 'location=00', 'c=BH1', '2017-01-01', '2017-01-04'],
                            rover_cmd='python -m rover', verbosity=0, delete_files=False, dev=True, log_verbosity=5)
        n_sncls = ListRetriever(config).run(config.args)
        assert n_sncls == 0, n_sncls
