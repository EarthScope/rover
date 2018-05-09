
import datetime
from sys import intern

from .utils import PushBackIterator, utc


EPOCH = datetime.datetime.utcfromtimestamp(0)
EPOCH_UTC = EPOCH.replace(tzinfo=utc)


def format_epoch(epoch):
    dt = datetime.datetime.fromtimestamp(epoch, utc)
    return datetime.datetime.strftime(dt, '%Y-%m-%dT%H:%M:%S.%f')


def parse_epoch(date):
    if date.endswith('Z'):
        date = date[:-1]
    dt = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
    return (dt - EPOCH).total_seconds()


class Coverage:
    """
    The data coverage (timespans) with the indx for a given sncl.

    This includes the logic to merge timespans.  The sncl parameter is
    a free string (or arbitrary object) and so this class can be used
    for SNCLS, SNCL + sampling rate, etc.
    """

    def __init__(self, tolerance, sncl, join=True):
        self._tolerance = tolerance
        self.sncl = sncl
        self.timespans = []
        self._join = join

    def add_epochs(self, begin, end):
        """
        Add a timesspan to those that already exist, merging if necessary.

        IMPORTANT: This assumes that the timestamps are added ordered
        by increasing start time - see builders that guarantee that.
        """
        if end - begin > self._tolerance:
            if not self._join or not self.timespans:
                self.timespans.append((begin, end))
            else:
                b, e = self.timespans[-1]
                if begin < b:
                    raise Exception('Unsorted start times')
                if begin <= e or begin - e < self._tolerance:
                    if end > e:
                        self.timespans[-1] = (b, end)
                else:
                    self.timespans.append((begin, end))

    def __str__(self):
        return '%s: %d timespans from %s to %s' % (
            self.sncl, len(self.timespans),
            format_epoch(self.timespans[0][0]) if self.timespans else '-',
            format_epoch(self.timespans[-1][1]) if self.timespans else '-'
        )

    def __eq__(self, other):
        try:
            return self.sncl == other.sncl and self.timespans == other.timespans
        except:
            return False

    def subtract(self, other):
        """
        Calculate the timespans for which this instance has data, but the
        other instance does not.
        """
        if not self.sncl == other.sncl:
            raise Exception('Cannot subtract mismatched availabilities')
        if not (self._join and other._join):
            raise Exception('Cannot subtract unjoined availabilities')
        us, them = PushBackIterator(iter(self.timespans)), PushBackIterator(iter(other.timespans))
        difference = Coverage(self._tolerance, self.sncl)
        while True:
            try:
                us_begin, us_end = next(us)
            except StopIteration:
                # we can return difference now, because there;s only more subtracting to do
                return difference
            try:
                them_begin, them_end = next(them)
            except StopIteration:
                # there's no more subtraction, so everything left goes into difference
                difference.add_epochs(us_begin, us_end)
                for (us_begin, us_end) in us:
                    difference.add_epochs(us_begin, us_end)
                return difference
            # we start before them
            if us_begin < them_begin:
                # we also end before them, so we're home free into the difference and
                # they live to try kill our next timespan
                if us_end <= them_begin:
                    difference.add_epochs(us_begin, us_end)
                    them.push((them_begin, them_end))
                # we end after they start, so we overlap.  save the initial part in
                # the difference and push the rest back for further consideration.
                else:
                    difference.add_epochs(us_begin, them_begin)
                    us.push((them_begin, us_end))
                    them.push((them_begin, them_end))
            # we start together
            elif us_begin == them_begin:
                # and we end first, so are completely wiped out, while they live to
                # perhaps delete more
                if us_end <= them_end:
                    them.push((them_begin, them_end))
                # but they end first.  so some of our timespan still lives to face
                # the next challenger.
                else:
                    us.push((them_end, us_end))
            # we start after them
            else:
                # if we also end before them, then we're deleted completely
                # while they continue to face out next timespan.
                if us_end <= them_end:
                    them.push((them_begin, them_end))
                # but we also end after them.  so some (perhaps all) of our timespan
                # remains to face their next timespan.
                else:
                    us.push((max(them_end, us_begin), us_end))


class BaseBuilder:

    def __init__(self, tolerance):
        self._tolerance = tolerance

    def _parse_timespans(self, timespans):
        for pair in timespans.split(','):
            pair = pair[1:-1]
            begin, end = map(float, pair.split(':'))
            yield begin, end


class SingleSNCLBuilder(BaseBuilder):
    """
    Sort the teimstamp information before creating the coverage.

    The mseedindex schema design make it difficult to sort this information in SQL.
    """

    def __init__(self, tolerance, sncl):
        super().__init__(tolerance)
        self._sncl = sncl
        self._timespans = []

    def add_timespans(self, timespans):
        for begin, end in self._parse_timespans(timespans):
            self._timespans.append((begin, end))

    def coverage(self):
        coverage = Coverage(self._tolerance, self._sncl)
        for begin, end in sorted(self._timespans):
            coverage.add_epochs(begin, end)
        return coverage


class MultipleSNCLBuilder(BaseBuilder):
    """
    Sort the teimstamp information before creating the coverage (and support multiple SNCLSs).

    The mseedindex schema design make it difficult to sort this information in SQL.
    """

    def __init__(self, tolerance, join=True):
        super().__init__(tolerance)
        self._join = join
        self._timespans = {}

    def add_timespans(self, sncl, timespans):
        sncl = intern(sncl)
        if sncl not in self._timespans:
            self._timespans[sncl] = []
        ts = self._timespans[sncl]
        for begin, end in self._parse_timespans(timespans):
            ts.append((begin, end))

    def coverages(self):
        for sncl in sorted(self._timespans.keys()):
            ts = self._timespans[sncl]
            coverage = Coverage(self._tolerance, sncl, join=self._join)
            for begin, end in sorted(ts):
                coverage.add_epochs(begin, end)
            yield coverage
