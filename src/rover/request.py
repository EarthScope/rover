
import operator
from functools import reduce
from re import sub, compile

from .args import mm, FORCEREQUEST
from .utils import parse_epoch

"""
Comparison of requests to check for overlap.
"""


def parse_request(path, regexp_only):
    """
    Read the request into memory, extracting the N_S_L_C and date data.
    """
    lines = []   # in-memory rather than a generator because we need to sort manually
    with open(path, 'r') as input:
        for line in input:
            try:
                line = line.strip()
                if line:
                    parts = line.split(' ')
                    sncl = parts[0:4]
                    if regexp_only:
                        if reduce(operator.or_, map(lambda x: '*' in x or '?' in x, sncl)):
                            # the outer sub here fixes things up so we match ? and * (we can't be explicit about
                            # * in the innermost sub because the middle sub would replace it).
                            sncl = list(map(lambda x: sub(r'\?', '?\\*',
                                                          sub(r'\*', '[A-Za-z0-9\-\?]*',
                                                              sub(r'\?', '[A-Za-z0-9\-\?]',
                                                                  x))), sncl))
                        else:
                            continue  # only regexps
                    dates = parts[4:]
                    assert len(dates) <= 2
                    while len(dates) < 2:
                        dates.append(None)
                    lines.append((' '.join(sncl), [tuple(dates)]))
            except:
                raise Exception(('Cannot parse "%s" in %s (experts can use %s ' +
                                 'at the risk of duplicating data in the repository)') %
                                (line, path, mm(FORCEREQUEST)))
    return lines


def unique(input):
    """
    If the same N_S_L_C occurs twice, merge the dates into a single entry.
    Needed for the fast comparison (of sorted files) to work correctly.
    """
    output = []
    for (sncl, dates) in sorted(input):
        if output and sncl == output[-1][0]:
            output[-1][1].append(dates[0])
        else:
            output.append((sncl, dates))
    return output


def overlapping_pair(pair1, pair2):
    """
    Check whether two pairs of dates (start and end) overlap.
    """
    # if either is open, they must overlap
    if not pair1 or not pair2:
        return True
    # if they're both lower bounds, they must overlap
    if len(pair1) == 1 and len(pair2) == 1:
        return True
    pair1 = list(map(parse_epoch, pair1))
    pair2 = list(map(parse_epoch, pair2))
    # dates1 is a range
    if len(pair1) == 2:
        # dates2 is a lower bound?
        if len(pair2) == 1:
            # if dates2 starts before dates1 ends, they overlap
            if pair2[0] < pair1[1]:
                return True
        else:
            # easier to find when they don't overlap, and then negate
            # they don't overlap if dates1 ends before dates2 starts, or vice versa
            if not (pair1[1] < pair2[0] or pair2[1] < pair1[0]):
                return True
    # dates1 is a lower bound
    else:
        # if dates1 starts before dates2 ends, they overlap
        if pair1[0] < pair2[1]:
            return True
    # if none of the above, no overlap
    return False


def overlapping_dates(dates1, dates2):
    """
    Check whether lists of pairs of dates contain any pairs that overlap.
    """
    # here dates are lists of tuples and we consider each possible pairing
    # which is O(n^2) but we don't expect to have many (i pray...)
    for pair1 in dates1:
        for pair2 in dates2:
            if overlapping_pair(pair1, pair2):
                return True
    return False


def format_dates(dates):
    """
    Format a list of date pairs, where the dates can be None if missing / open.
    """
    return ', '.join(map(lambda pair: ' - '.join(map(lambda date: date if date else 'open', pair)), dates))


class Regexps:
    """
    Encapsulate the regexps associated with a file.
    """

    def __init__(self, sncls, dates, path):
        self._sncls = sncls
        self._dates = dates
        self._path = path
        self._regexp = compile('(%s)' % '|'.join(sncls))

    def assert_no_overlap(self, sncl, dates, path):
        """
        Raise an exception on overlap.
        """
        # use a single "merged" regexp as gatekeeper and then run through each entry to find the
        # correct date.
        if self._regexp.match(sncl):
            for i in range(len(self._sncls)):
                if compile(self._sncls[i]).match(sncl) and overlapping_dates(self._dates[i], dates):
                    raise Exception('A pattern in %s matches an entry in %s (%s %s)' %
                                    (self._path, path, sncl, format_dates(dates)))


class RequestComparison:
    """
    Compare requests in two paths, checking for overlaps in requests.
    """

    def __init__(self, path1, path2):
        self._path1 = path1
        self._path2 = path2

    def _build_regexp(self, path):
        sncls_and_dates = list(parse_request(path, True))
        if sncls_and_dates:
            sncls, dates = list(zip(*sncls_and_dates))
            return Regexps(sncls, dates, path)
        else:
            return None

    def assert_no_overlap(self):
        """
        Compare the files and raise an exception on overlap.
        """
        # we need to be careful here, because the files can contain wildcards.
        # so we build regexps of the wildcards and test those, in addition to explicit equality.
        # note that we're careful to use regexp that match the regexp themselves.
        regexp1 = self._build_regexp(self._path1)
        regexp2 = self._build_regexp(self._path2)
        # we sort manually, in-memory, rather than on-disc because we don't trust the formatting to be regular
        values1 = iter(unique(parse_request(self._path1, False)))
        values2 = iter(unique(parse_request(self._path2, False)))
        # because the files are sorted we can do a fast O(n) comparison (think merge sort)
        try:
            sncl1, dates1 = next(values1)
            sncl2, dates2 = next(values2)
            while True:
                if regexp1:
                    regexp1.assert_no_overlap(sncl2, dates2, self._path2)
                if regexp2:
                    regexp2.assert_no_overlap(sncl1, dates1, self._path1)
                if sncl1 == sncl2 and overlapping_dates(dates1, dates2):
                    raise Exception('Overlap in %s and %s (%s %s and %s %s)' %
                                    (self._path1, self._path2, sncl1, format_dates(dates1), sncl2, format_dates(dates2)))
                if sncl1 < sncl2:
                    sncl1, dates1 = next(values1)
                else:
                    sncl2, dates2 = next(values2)
        except StopIteration:
            return False
