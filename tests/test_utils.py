import pytest
from tempfile import TemporaryDirectory

from rover.logs import init_log
from rover.utils import tidy_timestamp


def assert_timestamp(log, value, target):
    tidy = tidy_timestamp(log, value)
    assert tidy == target, tidy


def test_tidy_timestamp():
    with TemporaryDirectory() as dir:
        log = init_log(dir, '7M', 1, 5, 0, 'test', False, 0)[0]
        assert_timestamp(log, '2018-7-4', '2018-07-04T00:00:00.000000')
        assert_timestamp(log, '2018-7-4T1:2:3.456', '2018-07-04T01:02:03.456000')
        assert_timestamp(log, '2018-7-4T1:3', '2018-07-04T01:03:00.000000')
