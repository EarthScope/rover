
from rover.utils import format_epoch, parse_epoch


def loop_date(d1, known=None):
    e = parse_epoch(d1)
    if known is not None:
        assert e == known, (e, known)
    d2 = format_epoch(e)
    assert d1 == d2, (d1, d2)


def test_epoch():
    loop_date('1970-01-01T00:00:00.000000', known=0)
    loop_date('2018-05-19T01:23:45.123456')
