
from .utils import PushBackIterator, format_epoch


"""
Interface to the SNCL / timespan data in tsindex - how much data do we have
for particular channels?
"""


class Coverage:
    """
    The data coverage (timespans) with the index for a given sncl.

    This includes the logic to merge timespans.  The sncl parameter is
    a free string (or arbitrary object) and so this class can be used
    for SNCLS, SNCL + sampling rate, etc.
    """

    def __init__(self, log, frac_tolerance, sncl):
        self._log = log
        self._frac_tolerance = frac_tolerance
        self.sncl = sncl
        self.timespans = []
        self.samplerate = None

    def add_samplerate(self, samplerate):
        if samplerate:
            if self.samplerate:
                self.samplerate = min(self.samplerate, samplerate)
            else:
                self.samplerate = samplerate

    def add_epochs(self, begin, end, samplerate=None):
        """
        Add a timesspan to those that already exist, merging if necessary.

        IMPORTANT: This assumes that the timestamps are added ordered
        by increasing start time - see builders that guarantee that.
        """
        self.add_samplerate(samplerate)
        self.timespans.append((begin, end))

    def join(self):
        self._log.debug('Joining overlapping timespans')
        if self.timespans:  # avoid looking at samplerate if no data
            joined, tolerance = [], self.tolerance()
            for begin, end in self.timespans:
                if abs(end - begin) > tolerance:
                    if not joined:
                        joined.append((begin, end))
                    else:
                        b, e = joined[-1]
                        if begin < b:
                            raise Exception('Unsorted start times')
                        # do they overlap at all?
                        if abs(begin - e) < tolerance:
                            # if they do, and this extends previous, replace with maximal span
                            if end > e:
                                self._log.debug('Joining %d-%d and %d-%d' % (begin, end, b, e))
                                joined[-1] = (b, end)
                        # no they don't overlap
                        else:
                            joined.append((begin, end))
                else:
                    self._log.debug('Disarding %d-%d (too small)' % (begin, end))
            self.timespans = joined

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

    def tolerance(self):
        if not self.samplerate:
            raise Exception('No samplerate available')
        return self._frac_tolerance / self.samplerate

    def subtract(self, other):
        """
        Calculate the timespans for which this instance has data, but the
        other instance does not.
        """
        if not self.sncl == other.sncl:
            raise Exception('Cannot subtract mismatched availabilities')
        if not other.timespans:  # subtracting zero (avoid checking samplerate)
            return self

        # minimal samplerate
        self.add_samplerate(other.samplerate)
        other.add_samplerate(self.samplerate)
        tolerance = self.tolerance()
        # simplify the work by compressing both
        self.join()
        other.join()

        us, them = PushBackIterator(iter(self.timespans)), PushBackIterator(iter(other.timespans))
        difference = Coverage(self._log, self._frac_tolerance, self.sncl)
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

            # we start together
            if abs(us_begin - them_begin) < tolerance:
                # if we end together too, there's nothing to do
                if abs(us_end - them_end) < tolerance:
                    pass
                # if we end first, so are completely wiped out, while they live to
                # perhaps delete more
                elif us_end < them_end:
                    them.push((them_begin, them_end))
                # but they end first.  so some of our timespan still lives to face
                # the next challenger.
                else:
                    us.push((them_end, us_end))
            # we start before them
            elif us_begin < them_begin:
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


# builders are needed to buffer the data read from the database and sort it,
# this is because:
# (1) the add_epochs() method requires sorted data to correctly merge timespans
# (2) the timespans are squashed into strings that are not easy to use at the SQL
#     level (so we need to read and then sort in-memory).


class BaseBuilder:
    """
    Shared functionality for all coverage builders.
    """

    def __init__(self, log, frac_tolerance):
        self._log = log
        self._frac_tolerance = frac_tolerance

    def _parse_timespans(self, timespans):
        for pair in timespans.split(','):
            pair = pair[1:-1]
            begin, end = map(float, pair.split(':'))
            yield begin, end


class SingleSNCLBuilder(BaseBuilder):
    """
    Sort the timestamp information before creating the coverage (for a single SNCL)

    The mseedindex schema design makes it difficult to sort this information in SQL.
    """

    def __init__(self, log, frac_tolerance, sncl):
        super().__init__(log, frac_tolerance)
        self._sncl = sncl
        self._timespans = []

    def add_timespans(self, timespans, samplerate=None):
        for begin, end in self._parse_timespans(timespans):
            self._timespans.append((begin, end, samplerate))

    def coverage(self):
        coverage = Coverage(self._log, self._frac_tolerance, self._sncl)
        for begin, end, samplerate in sorted(self._timespans):
            coverage.add_epochs(begin, end, samplerate)
        return coverage


class MultipleSNCLBuilder(BaseBuilder):
    """
    Sort the teimstamp information before creating the coverage (for multiple SNCLSs).

    The mseedindex schema design makes it difficult to sort this information in SQL.
    """

    def __init__(self, log, frac_tolerance, join=True):
        super().__init__(log, frac_tolerance)
        self._join = join
        self._timespans = {}

    def add_timespans(self, sncl, timespans, samplerate=None):
        if sncl not in self._timespans:
            self._timespans[sncl] = []
        ts = self._timespans[sncl]
        for begin, end in self._parse_timespans(timespans):
            ts.append((begin, end, samplerate))

    def coverages(self):
        for sncl in sorted(self._timespans.keys()):
            ts = self._timespans[sncl]
            coverage = Coverage(self._log, self._frac_tolerance, sncl)
            for begin, end, samplerate in sorted(ts):
                coverage.add_epochs(begin, end, samplerate)
            if self._join:
                coverage.join()
            yield coverage
