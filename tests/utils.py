
from os.path import join, exists
from sys import version_info

if version_info[0] >= 3:
    from tempfile import TemporaryDirectory
else:
    from backports.tempfile import TemporaryDirectory

from rover.args import DEFAULT_LEAPURL, DEFAULT_LEAPEXPIRE, DEFAULT_HTTPTIMEOUT, DEFAULT_HTTPRETRIES
from rover.logs import init_log
from rover.utils import check_leap

from .test_utils import WindowsTemp


def test_download_leap():
    with WindowsTemp(TemporaryDirectory) as dir:
        log = init_log(dir, 7, 1, 5, 0, 'test', False, 0)[0]
        path = join(dir, 'leap.txt')
        check_leap(True, DEFAULT_LEAPEXPIRE, path, DEFAULT_LEAPURL, DEFAULT_HTTPTIMEOUT, DEFAULT_HTTPRETRIES, log)
        assert exists(path)
