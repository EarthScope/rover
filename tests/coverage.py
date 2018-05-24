
from sys import version_info

if version_info[0] >= 3:
    from tempfile import TemporaryDirectory
else:
    from backports.tempfile import TemporaryDirectory

from rover.logs import init_log
from rover.coverage import Coverage
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



# rather than try to work out what tests are what in my head, the test
# framework itself prints an image of the test and the result.  hopefully
# the two can be checked by eye and then the result copied into the
# expected value.


def build_coverage(log, width, gap, offset):
    total = width + gap
    left = (offset % total) - width
    indices = []
    while left < 6:
        right = left + width
        indices.append((max(left, 0), min(right, 6)))
        left += total
    return indices_to_coverage(log, indices)


def coverage_to_str(coverage):
    return '(' + ','.join(map(lambda be: '(%d,%d)' % be, coverage.timespans)) + ')'


def indices_to_coverage(log, indices):
    # 0.5 here so no overlap between integers
    coverage = Coverage(log, 0.5, 'N.S.L.C')
    for (begin, end) in indices:
        if begin != end:
            coverage.add_epochs(begin, end, 1)
    return coverage


def include(indices, hour):
    for (begin, end) in indices:
        if begin < hour < end:
            return True
    return False


def print_labels():
    print('%9s ' % '', end='')
    for i in range(6):
        print('%d    ' % i, end='')
    print(6)


def print_coverage(title, coverage):
    print('%9s ' % title, end='')
    for i in range(0, 6):
        print('|', end='')
        if include(coverage.timespans, i+0.5):
            print('====', end='')
        else:
            print('    ', end='')
    print('|')


def run(log,
        width_index, gap_index, offset_index,
        width_avail, gap_avail, offset_avail,
        expected):
    index = build_coverage(log, width_index, gap_index, offset_index)
    avail = build_coverage(log, width_avail, gap_avail, offset_avail)
    print_labels()
    print_coverage('index', index)
    print_coverage('avail', avail)
    missing = avail.subtract(index)
    print_coverage('missing', missing)
    target = indices_to_coverage(log, expected)
    assert target == missing, coverage_to_str(missing)
    print()


def test_coverage():
    with TemporaryDirectory() as dir:
        log = init_log(dir, 10, 1, 5, 4, 'coverage', False, 1)
        run(log, 2, 1, -1, 3, 2, 0, ((2,3),))
        run(log, 2, 1, -1, 3, 2, 1, ((5,6),))
        run(log, 2, 1, -1, 3, 2, 2, ((5,6),))
        run(log, 2, 1, -1, 1, 1, 0, ((5,6),))
        run(log, 2, 1, 0, 1, 1, 0, ((3,4),))
        run(log, 2, 1, 1, 1, 1, 0, ((1,2),))
        run(log, 1, 2, 0, 1, 2, 0, tuple())
        run(log, 1, 2, 1, 1, 2, 0, ((2,3),(5,6)))
        run(log, 1, 2, 2, 1, 2, 0, ((2,3),(5,6)))
        run(log, 1, 2, 3, 1, 2, 0, tuple())
        run(log, 2, 2, 0, 2, 2, 0, tuple())
        run(log, 2, 2, 0, 2, 2, 1, ((0,1),(4,5),))
        run(log, 2, 2, 0, 2, 2, 2, ((0,2),(4,6)))
        run(log, 1, 1, 0, 3, 2, 0, ((2,3),(4,5)))
        run(log, 1, 1, 0, 3, 2, 1, ((0,1),(4,5)))
