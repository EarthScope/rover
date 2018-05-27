
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
    return indices


def coverage_to_str(coverage):
    return '(' + ','.join(map(lambda be: '(%d,%d)' % be, coverage.timespans)) + ')'


def indices_to_coverage(log, tolerance, indices):
    coverage = Coverage(log, tolerance, 'N.S.L.C')
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


def run_explicit(log, tolerance, index, avail, expected):
    """
    A bad test looks like:

          0    1    2    3    4    5    6
    index |====|====|    |====|====|    |
    avail |    |====|    |====|    |====|
  missing |    |    |    |    |    |====|

    where, for exmaple, index has data from 0-1 but it's not in missing
    """
    index = indices_to_coverage(log, tolerance, index)
    avail = indices_to_coverage(log, tolerance, avail)
    print_labels()
    print_coverage('index', index)
    print_coverage('avail', avail)
    missing = avail.subtract(index)
    print_coverage('missing', missing)
    expected = indices_to_coverage(log, tolerance, expected)
    assert expected == missing, coverage_to_str(missing)
    print()


def run(log, tolerance,
        width_index, gap_index, offset_index,
        width_avail, gap_avail, offset_avail,
        expected):
    run_explicit(log, tolerance,
                 build_coverage(log, width_index, gap_index, offset_index),
                 build_coverage(log, width_avail, gap_avail, offset_avail),
                 expected)


def test_coverage():
    with TemporaryDirectory() as dir:
        log = init_log(dir, 10, 1, 5, 4, 'coverage', False, 1)
        run(log, 0.5, 2, 1, -1, 3, 2, 0, ((2,3),))
        run(log, 0.5, 2, 1, -1, 3, 2, 1, ((5,6),))
        run(log, 0.5, 2, 1, -1, 3, 2, 2, ((5,6),))
        run(log, 0.5, 2, 1, -1, 1, 1, 0, ((5,6),))
        run(log, 0.5, 2, 1, 0, 1, 1, 0, ((3,4),))
        run(log, 0.5, 2, 1, 1, 1, 1, 0, ((1,2),))
        run(log, 0.5, 1, 2, 0, 1, 2, 0, tuple())
        run(log, 0.5, 1, 2, 1, 1, 2, 0, ((2,3),(5,6)))
        run(log, 0.5, 1, 2, 2, 1, 2, 0, ((2,3),(5,6)))
        run(log, 0.5, 1, 2, 3, 1, 2, 0, tuple())
        run(log, 0.5, 2, 2, 0, 2, 2, 0, tuple())
        run(log, 0.5, 2, 2, 0, 2, 2, 1, ((0,1),(4,5),))
        run(log, 0.5, 2, 2, 0, 2, 2, 2, ((0,2),(4,6)))
        run(log, 0.5, 1, 1, 0, 3, 2, 0, ((2,3),(4,5)))
        run(log, 0.5, 1, 1, 0, 3, 2, 1, ((0,1),(4,5)))

# with tolerance 1.5 these overlap
# (this was a bug with rover retrieve IU_ANMO_3?_* 2016-01-01T20:00:00 2016-01-02T04:00:00)
#         0    1    2    3    4    5    6
#   index |    |====|====|====|    |    |
#   avail |    |    |    |====|====|    |
# missing |    |    |    |    |    |    |
        run_explicit(log, 1.5, [(1,4)], [(3,5)], [])

