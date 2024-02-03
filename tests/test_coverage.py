import pytest
from tempfile import TemporaryDirectory
from random import randint, seed

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
    while left < 10:
        right = left + width
        indices.append((max(left, 0), min(right, 10)))
        left += total
    return indices


def coverage_to_str(coverage):
    return '(' + ','.join(map(lambda be: '(%g,%g)' % be, coverage.timespans)) + ')'


def indices_to_coverage(log, tolerance, increment, indices):
    coverage = Coverage(log, tolerance, increment, 'N.S.L.C')
    for (begin, end) in indices:
        if begin != end:
            coverage.add_epochs(begin, end, 1)
    return coverage


def include(indices, hour):
    for (begin, end) in indices:
        if begin <= hour <= end:
            return True
    return False


def print_labels():
    print('%9s ' % '', end='')
    for i in range(10):
        print('%d    ' % i, end='')
    print(10)


def print_coverage(title, coverage):
    print('%9s ' % title, end='')
    for i in range(0, 11):
        if i:
            if include(coverage.timespans, i-1) and include(coverage.timespans, i):
                print('====', end='')
            else:
                print('    ', end='')
        if include(coverage.timespans, i):
            print('#', end='')
        else:
            print('.', end='')
    print()


def run_explicit(log, tolerance, increment, index, avail, expected):
    """
    A bad test looks like:

          0    1    2    3    4    5    6    7    8    9    10
    index .    #====#    .    #====#    .    #====#    .    .
    avail .    .    #====#    .    #====#    .    #====#    .
  missing .    .    .    .    .    .    #    .    .    #    .

    where, for example, avail has data at 3 but it's not in missing
    """
    index = indices_to_coverage(log, tolerance, increment, index)
    avail = indices_to_coverage(log, tolerance, increment, avail)
    missing = avail.subtract(index)
    expected = indices_to_coverage(log, tolerance, increment, expected)
    if True or expected != missing:
        print()
        print_labels()
        print_coverage('index', index)
        print_coverage('avail', avail)
        print_coverage('missing', missing)
    assert expected == missing, coverage_to_str(missing)


def run(log, tolerance, increment,
        width_index, gap_index, offset_index,
        width_avail, gap_avail, offset_avail,
        expected):
    run_explicit(log, tolerance, increment,
                 build_coverage(log, width_index, gap_index, offset_index),
                 build_coverage(log, width_avail, gap_avail, offset_avail),
                 expected)


def test_coverage():
    with TemporaryDirectory() as dir:
        log = init_log(dir, '10M', 1, 5, 4, 'coverage', False, 1)[0]
        run(log, 0.5, 0.5, 0, 10, 0, 3, 2, 0, ((2,5),(7,10)))
        run(log, 0.5, 0.5, 2, 1, -1, 3, 2, 0, ())
        run(log, 0.5, 0.5, 2, 1, -1, 3, 2, 1, ())
        run(log, 0.5, 0.5, 2, 1, -1, 3, 2, 2, ())
        run(log, 0.5, 0.5, 2, 1, -1, 1, 1, 0, ())
        run(log, 0.5, 0.5, 2, 1, 0, 1, 1, 0, ((9.5,10),))
        run(log, 0.5, 0.5, 2, 1, 1, 1, 1, 0, ())
        run(log, 0.5, 0.5, 1, 2, 0, 1, 2, 0, ())
        run(log, 0.5, 0.5, 1, 2, 1, 1, 2, 0, ((2,2.5),(5,5.5),(8,8.5)))
        run(log, 0.5, 0.5, 1, 2, 2, 1, 2, 0, ((2.5,3),(5.5,6),(8.5,9)))
        run(log, 0.5, 0.5, 1, 2, 3, 1, 2, 0, ())
        run(log, 0.5, 0.5, 2, 2, 0, 2, 2, 0, ())
        run(log, 0.5, 0.5, 2, 2, 0, 2, 2, 1, ((0,1),(4.5,5),(8.5,9)))
        run(log, 0.5, 0.5, 2, 2, 0, 2, 2, 2, ((0,1.5),(4.5,5.5),(8.5,10)))
        run(log, 0.5, 0.5, 1, 1, 0, 3, 2, 0, ())
        run(log, 0.5, 0.5, 1, 1, 0, 3, 2, 1, ((0,0.5),))

# with tolerance 1.5 these overlap
# (this was a bug with rover retrieve IU_ANMO_3?_* 2016-01-01T20:00:00 2016-01-02T04:00:00)
#         0    1    2    3    4    5    6
#   index |    |====|====|====|    |    |
#   avail |    |    |    |====|====|    |
# missing |    |    |    |    |    |    |
        run_explicit(log, 1.5, 0.5, [(1,4)], [(3,5)], [])
# more of same (in retrospect these seem weird - we shouldn't be using a tolerance of 1.5!)
        seed(42)
        for i in range(100):
            # available of length at least 2 (so > tolerance)
            avail_start = randint(0, 4)
            avail_end = randint(avail_start + 2, 6)
            # index must start before one after start of avail (so before, within tolerance)
            index_start = randint(0, min(4, avail_start+1))
            # and must end with a width of at least 2, and at least one before end (so after, within tolerance)
            index_end = randint(max(avail_end-1, index_start+2), 6)
            run_explicit(log, 1.5, 0.5, [(index_start, index_end)], [(avail_start, avail_end)], [])
