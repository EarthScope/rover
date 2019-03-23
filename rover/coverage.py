
from .utils import PushBackIterator, format_epoch, parse_epoch

"""
Interface to the N_S_L_C / timespan data in tsindex - how much data do we have
for particular channels?
"""


class Coverage:
    """
    The data coverage (timespans) with the index for a given N_S_L_C.

    This includes the logic to merge timespans.  The N_S_L_C parameter is
    a free string (or arbitrary object) and so this class can be used
    for N_S_L_C, N_S_L_C + sampling rate, etc.
    """

    def __init__(self, log, frac_tolerance, frac_increment, sncl):
        self._log = log
        self._frac_tolerance = frac_tolerance
        self._frac_increment = frac_increment
        self.sncl = sncl
        self.timespans = []
        self.samplerate = None

    def add_samplerate(self, samplerate):
        if samplerate is not None:
            if self.samplerate is not None:
                self.samplerate = min(self.samplerate, samplerate)
            else:
                # a samplerate of zero seems to be used for logging or other
                # state-of-health channels, so use a large value in that case
                self.samplerate = samplerate if samplerate else 10000

    def add_epochs(self, start, end, samplerate=None):
        """
        Add a timespan to those that already exist, merging if necessary.

        IMPORTANT: This assumes that the timestamps are added ordered
        by increasing start time - see builders that guarantee that.
        """
        self.add_samplerate(samplerate)
        self.timespans.append((start, end))

    def join(self):
        self._log.debug('Joining overlapping timespans')
        if self:  # avoid looking at samplerate if no data
            joined, (tolerance, increment) = [], self.tolerances()
            for start, end in self.timespans:
                if not joined:
                    joined.append((start, end))
                else:
                    b, e = joined[-1]
                    if start < b:
                        raise Exception('Unsorted start times')
                    # do they overlap at all?
                    if self.samplerate == 0:
                        # Channels with 0 sample rate must always be merged.
                        self._log.debug('Joining channel with sample rate of zero.')
                        joined[-1]=(b, end)
                    elif abs(start - e) < 1.0 / self.samplerate + tolerance:
                        # if they do, and this extends previous, replace with maximal span
                        if end > e:
                            self._log.debug('Joining %d-%d and %d-%d' % (start, end, b, e))
                            joined[-1] = (b, end)
                    # no they don't overlap
                    else:
                        joined.append((start, end))
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

    def __bool__(self):
        return bool(self.timespans)

    def tolerances(self):
        if self.samplerate is None:
            raise Exception('Sample rate is not available.')
        if self.samplerate == 0:
            return 0.0, 0.0
        return self._frac_tolerance / self.samplerate, self._frac_increment / self.samplerate

    def subtract(self, other):
        """
        Calculate the timespans for which this instance has data, but the
        other instance does not.
        """
        if not self.sncl == other.sncl:
            raise Exception('Cannot subtract mismatched availabilities')
        if not other:  # subtracting zero (avoid checking samplerate)
            return self

        # minimal samplerate
        self.add_samplerate(other.samplerate)
        other.add_samplerate(self.samplerate)
        tolerance, increment = self.tolerances()
        # simplify the work by compressing both
        self.join()
        other.join()

        us, them = PushBackIterator(iter(self.timespans)), PushBackIterator(iter(other.timespans))
        difference = Coverage(self._log, self._frac_tolerance, self._frac_increment, self.sncl)
        difference.add_samplerate(self.samplerate)
        while True:
            try:
                us_start, us_end = next(us)
            except StopIteration:
                # we can return difference now, because there's only more subtracting to do
                return difference
            try:
                them_start, them_end = next(them)
            except StopIteration:
                # there's no more subtraction, so everything left goes into difference
                if us_end - us_start >= tolerance:
                    difference.add_epochs(us_start, us_end)
                for (us_start, us_end) in us:
                    if us_end - us_start >= tolerance:
                        difference.add_epochs(us_start, us_end)
                return difference

            # we start together
            if abs(us_start - them_start) < tolerance:
                # if we end together too, there's nothing to do
                if abs(us_end - them_end) < tolerance:
                    pass
                # if we end first, so are completely wiped out, while they live to
                # perhaps delete more
                elif us_end < them_end:
                    them.push((them_start, them_end))
                # but they end first.  so some of our timespan still lives to face
                # the next challenger.
                else:
                    # since this is a real difference we need to nudge forwards so
                    # that we avoid including the end point of them again.
                    us.push((them_end + increment, us_end))
            # we start before them (difference must be larger than tolerance - see above)
            elif us_start < them_start:
                # we also end before them, so we're home free into the difference and
                # they live to try kill our next timespan
                if us_end < them_start:
                    difference.add_epochs(us_start, us_end)
                    them.push((them_start, them_end))
                # we end after they start, so we overlap.  save the initial part in
                # the difference and push the rest back for further consideration.
                else:
                    # is (us_start, them_start - increment) worth adding?
                    if them_start - increment - us_start >= tolerance:
                        difference.add_epochs(us_start, them_start - increment)
                    if us_end - them_start > tolerance:
                        us.push((them_start, us_end))
                    them.push((them_start, them_end))
            # we start after them
            else:
                # if we also end before them, then we're deleted completely
                # while they continue to face our next timespan.
                # (this is tricky - we can end slightly after, if it's within tolerance)
                if us_end - them_end < tolerance:
                    them.push((them_start, them_end))
                # but we also end after them.  so some (perhaps all) of our timespan
                # remains to face their next timespan.
                else:
                    # again, we need to nudge forwards beyond them to avoid
                    # re-including the point
                    us.push((max(them_end + increment, us_start), us_end))


# builders are needed to buffer the data read from the database and sort it,
# this is because:
# (1) the add_epochs() method requires sorted data to correctly merge timespans
# (2) the timespans are squashed into strings that are not easy to use at the SQL
#     level (so we need to read and then sort in-memory).


class BaseBuilder:
    """
    Shared functionality for all coverage builders.
    """

    def __init__(self, log, frac_tolerance, frac_increment):
        self._log = log
        self._frac_tolerance = frac_tolerance
        self._frac_increment = frac_increment

    def _parse_timespans(self, timespans):
        if timespans is None:
            raise Exception('Unexpected NULL reading timespans')
        for pair in timespans.split(','):
            inner = pair[1:-1]
            if pair[0] == '[':
                start, end = map(float, inner.split(':'))
            elif pair[0] == '<':
                start, end = map(parse_epoch, inner.split(' '))
            else:
                raise Exception('Unexpected timespans format: "%s"' % pair)
            yield start, end


class SingleSNCLBuilder(BaseBuilder):
    """
    Sort the timestamp information before creating the coverage (for a single N_S_C_C)

    The mseedindex schema design makes it difficult to sort this information in SQL.
    """

    def __init__(self, log, frac_tolerance, frac_increment, sncl):
        super().__init__(log, frac_tolerance, frac_increment)
        self._sncl = sncl
        self._timespans = []

    def add_timespans(self, timespans, samplerate=None):
        for start, end in self._parse_timespans(timespans):
            self._timespans.append((start, end, samplerate))

    def coverage(self):
        coverage = Coverage(self._log, self._frac_tolerance, self._frac_increment, self._sncl)
        for start, end, samplerate in sorted(self._timespans):
            coverage.add_epochs(start, end, samplerate)
        return coverage


class MultipleSNCLBuilder(BaseBuilder):
    """
    Sort the timestamp information before creating the coverage (for multiple N_S_L_Cs).

    The mseedindex schema design makes it difficult to sort this information in SQL.
    """

    def __init__(self, log, frac_tolerance, frac_increment, join=True):
        super().__init__(log, frac_tolerance, frac_increment)
        self._join = join
        self._timespans = {}

    def add_timespans(self, sncl, timespans, samplerate=None):
        if sncl not in self._timespans:
            self._timespans[sncl] = []
        ts = self._timespans[sncl]
        for start, end in self._parse_timespans(timespans):
            ts.append((start, end, samplerate))

    def coverages(self):
        for sncl in sorted(self._timespans.keys()):
            ts = self._timespans[sncl]
            coverage = Coverage(self._log, self._frac_tolerance, self._frac_increment, sncl)
            for start, end, samplerate in sorted(ts):
                coverage.add_epochs(start, end, samplerate)
            if self._join:
                coverage.join()
            yield coverage
