
from tempfile import TemporaryDirectory
from tempfile import mktemp
from os.path import join

from rover.sqlite import init_db
from rover.download import Downloader
from rover.logs import init_log
from .test_utils import find_root, assert_files


def test_dlownload():
    root = find_root()
    with TemporaryDirectory() as dir:
        log = init_log(dir, 7, 1, 5, 3, 'test', False, 0)
        dbpath = mktemp(dir=dir)
        db = init_db(dbpath, log)
        downloader = Downloader(db, dir, join(root, '..', 'mseedindex', 'mseedindex'), dbpath, dir,
                                False, None, None, None, 1, False, log)
        downloader.download('http://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2010-02-27T06:30:00.000&end=2010-02-27T10:30:00.000')
        assert_files(join(dir, 'IU'), '2010')
        assert_files(join(dir, 'IU', '2010'), '58')
        assert_files(join(dir, 'IU', '2010', '58'), 'ANMO.IU.2010.58')
        n = db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 1, n  # todo is this right?  just one?
