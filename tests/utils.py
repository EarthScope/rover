
from os.path import join, exists
from sys import version_info

if version_info[0] >= 3:
    from tempfile import TemporaryDirectory
else:
    from backports.tempfile import TemporaryDirectory

from rover.args import DEFAULT_LEAPURL, DEFAULT_LEAPEXPIRE, DEFAULT_HTTPTIMEOUT, DEFAULT_HTTPRETRIES
from rover.logs import init_log
from rover.utils import check_leap, tidy_timestamp

from .test_utils import WindowsTemp


def test_download_leap():
    with WindowsTemp(TemporaryDirectory) as dir:
        log = init_log(dir, '7M', 1, 5, 0, 'test', False, 0)[0]
        path = join(dir, 'leap.txt')
        check_leap(True, DEFAULT_LEAPEXPIRE, path, DEFAULT_LEAPURL, DEFAULT_HTTPTIMEOUT, DEFAULT_HTTPRETRIES, log)
        assert exists(path)


def assert_timestamp(log, value, target):
    tidy = tidy_timestamp(log, value)
    assert tidy == target, tidy


def test_tidy_timestamp():
    with WindowsTemp(TemporaryDirectory) as dir:
        log = init_log(dir, '7M', 1, 5, 0, 'test', False, 0)[0]
        assert_timestamp(log, '2018-7-4', '2018-07-04T00:00:00.000000')
        assert_timestamp(log, '2018-7-4T1:2:3.456', '2018-07-04T01:02:03.456000')
        assert_timestamp(log, '2018-7-4T1:3', '2018-07-04T01:03:00.000000')
