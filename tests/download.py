
from os.path import join
from tempfile import TemporaryDirectory

from rover.download import Downloader
from .test_utils import find_root, assert_files, TestConfig


def test_download():
    with TemporaryDirectory() as dir:
        config = TestConfig(dir)
        downloader = Downloader(config)
        downloader.run('http://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2010-02-27T06:30:00.000&end=2010-02-27T10:30:00.000')
        mseed_dir = config.args.mseed_dir
        assert_files(join(mseed_dir, 'IU'), '2010')
        assert_files(join(mseed_dir, 'IU', '2010'), '58')
        assert_files(join(mseed_dir, 'IU', '2010', '58'), 'ANMO.IU.2010.58')
        n = config.db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 1, n  # todo is this right?  just one?
