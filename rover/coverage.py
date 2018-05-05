
from .utils import format_time, PushBackIterator


class Sncl:

    def __init__(self, net, sta, loc, cha):
        self.net = net
        self.sta = sta
        self.loc = loc
        self.cha = cha

    def __eq__(self, other):
        try:
            return self.net == other.net and self.sta == other.sta and self.loc == other.loc and self.cha == other.cha
        except:
            return False

    def __str__(self):
        return '%s.%s.%s.%s' % (self.net, self.sta, self.loc, self.cha)

    def to_url_params(self):
        return 'net=%s&sta=%s&loc=%s&cha=%s' % (self.net, self.sta, self.loc, self.cha)


class Coverage:
    """
    A SNCL and associated timespans.

    The timespans are ordered and do not overlap (they are merged
    as they are added).
    """

    def __init__(self, tolerance, sncl):
        self._tolerance = tolerance
        self.sncl = sncl
        self.timespans = []

    def add_timespan(self, begin, end):
        """
        Add a timesspan to those that already exist, merging if
        necessary.

        IMPORTANT: This assumes that the timestamps are added ordered
        by increasing start time.
        """
        if not self.timespans:
            self.timespans.append((begin, end))
        else:
            b, e = self.timespans[-1]
            if begin < b:
                raise Exception('Unsorted start times')
            if begin <= e or (begin - e).total_seconds() < self._tolerance:
                if end > e:
                    self.timespans[-1] = (b, end)
            else:
                self.timespans.append((begin, end))

    def __str__(self):
        return '%s: %d timespans from %s to %s' % (
            self.sncl, len(self.timespans),
            format_time(self.timespans[0][0]) if self.timespans else '-',
            format_time(self.timespans[-1][1]) if self.timespans else '-'
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
        # set_trace()
        if not self.sncl == other.sncl:
            raise Exception('Cannot subtract mismatched availabilities')
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
                difference.add_timespan(us_begin, us_end)
                for (us_begin, us_end) in us:
                    difference.add_timespan(us_begin, us_end)
                return difference
            # we start before them
            if us_begin < them_begin:
                # we also end before them, so we're home free into the difference and
                # they live to try kill our next timespan
                if us_end <= them_begin:
                    difference.add_timespan(us_begin, us_end)
                    them.push((them_begin, them_end))
                # we end after they start, so we overlap.  save the initial part in
                # the difference and push the rest back for further consideration.
                else:
                    difference.add_timespan(us_begin, them_begin)
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
