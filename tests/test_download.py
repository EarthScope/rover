import pytest
from tempfile import TemporaryDirectory
from os.path import join

from rover.args import DATADIR
from rover.download import Downloader
from .shared_utils import assert_files, TestConfig


def test_download():
    with TemporaryDirectory() as dir:
        config = TestConfig(dir)
        downloader = Downloader(config)
        downloader.run(['http://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2010-02-27T06:30:00.000&end=2010-02-27T10:30:00.000'])
        data_dir = config.arg(DATADIR)

        assert_files(join(data_dir, 'IU'), '2010')
        assert_files(join(data_dir, 'IU', '2010'), '058')
        assert_files(join(data_dir, 'IU', '2010', '058'), 'ANMO.IU.2010.058')

        n = config.db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 1, n
