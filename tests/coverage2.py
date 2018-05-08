
from rover.coverage2 import parse_epoch, format_epoch


def loop_date(d1):
    e = parse_epoch(d1)
    d2 = format_epoch(e)
    assert d1 == d2, (d1, d2)


def test_epoch():
    loop_date('1970-01-01T00:00:00.000000')
    loop_date('2018-05-19T01:23:45.123456')
