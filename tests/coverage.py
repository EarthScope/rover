
from datetime import datetime

from rover.coverage import Coverage, Sncl


# rather than try to work out what tests are what in my head, the test
# framework itself prints an image of the test and the result.  hopefully
# the two can be checked by eye and then the result copied into the
# expected value.


def build_coverage(width, gap, offset):
    total = width + gap
    left = (offset % total) - width
    indices = []
    while left < 6:
        right = left + width
        indices.append((max(left, 0), min(right, 6)))
        left += total
    return indices_to_coverage(indices)


def coverage_to_indices(coverage):
    for timespan in coverage.timespans:
        yield timespan[0].hour, timespan[1].hour


def coverage_to_str(coverage):
    return '(' + ','.join(map(lambda be: '(%d,%d)' % be, coverage_to_indices(coverage))) + ')'


def indices_to_coverage(indices):
    coverage = Coverage(1, Sncl('N', 'S', 'L', 'C'))
    for (begin, end) in indices:
        if begin != end:
            coverage.add_timespan(datetime(2000, 1, 1, begin), datetime(2000, 1, 1, end))
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
    indices = list(coverage_to_indices(coverage))
    print('%9s ' % title, end='')
    for i in range(0, 6):
        print('|', end='')
        if include(indices, i+0.5):
            print('====', end='')
        else:
            print('    ', end='')
    print('|')


def run(width_index, gap_index, offset_index,
        width_avail, gap_avail, offset_avail,
        expected):
    index = build_coverage(width_index, gap_index, offset_index)
    avail = build_coverage(width_avail, gap_avail, offset_avail)
    print_labels()
    print_coverage('index', index)
    print_coverage('avail', avail)
    missing = avail.subtract(index)
    print_coverage('missing', missing)
    target = indices_to_coverage(expected)
    assert target == missing, coverage_to_str(missing)
    print()


def test_coverage():
    run(2, 1, -1, 3, 2, 0, ((2,3),))
    run(2, 1, -1, 3, 2, 1, ((5,6),))
    run(2, 1, -1, 3, 2, 2, ((5,6),))
    run(2, 1, -1, 1, 1, 0, ((5,6),))
    run(2, 1, 0, 1, 1, 0, ((3,4),))
    run(2, 1, 1, 1, 1, 0, ((1,2),))
    run(1, 2, 0, 1, 2, 0, tuple())
    run(1, 2, 1, 1, 2, 0, ((2,3),(5,6)))
    run(1, 2, 2, 1, 2, 0, ((2,3),(5,6)))
    run(1, 2, 3, 1, 2, 0, tuple())
    run(2, 2, 0, 2, 2, 0, tuple())
    run(2, 2, 0, 2, 2, 1, ((0,1),(4,5),))
    run(2, 2, 0, 2, 2, 2, ((0,2),(4,6)))
    run(1, 1, 0, 3, 2, 0, ((2,3),(4,5)))
    run(1, 1, 0, 3, 2, 1, ((0,1),(4,5)))
