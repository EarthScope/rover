
from tempfile import TemporaryDirectory
from os.path import join, exists

from rover.config import DEFAULT_LEAPURL, DEFAULT_LEAPEXPIRE
from rover.logs import init_log
from rover.utils import check_leap


def test_download_leap():
    with TemporaryDirectory() as dir:
        log = init_log(dir, 7, 1, 5, 0, 'test')
        path = join(dir, 'leap.txt')
        check_leap(True, DEFAULT_LEAPEXPIRE, path, DEFAULT_LEAPURL, log)
        assert exists(path)