
from os import unlink, makedirs
from os.path import join, exists
from re import match
from shutil import copyfile

from .utils import uniqueish, create_parents, canonify, post_to_file, unique_filename, run, parse_time, format_time
from .config import RETRIEVE
from .sqlite import SqliteSupport


RETRIEVEFILE = 'rover_retrieve'


class Availability:  # todo - more general name

    def __init__(self, tolerance, network, station, location, channel):
        self._tolerance = tolerance
        self.network = network
        self.station = station
        self.location = location
        self.channel = channel
        self.timespans = []

    def is_sncl(self, n, s, l, c):
        return self.network == n and self.station == s and self.location == l and self.channel == c

    def add_timespan(self, begin, end):
        if not self.timespans:
            self.timespans.append((begin, end))
        else:
            b, e = self.timespans[-1]
            if begin < b:
                raise Exception('Unsorted availability')
            if begin <= e or (begin - e).total_seconds() < self._tolerance:
                if end > e:
                    self.timespans[-1] = (b, end)
            else:
                self.timespans.append((begin, end))

    def __str__(self):
        return '%s.%s.%s.%s: %d timespans from %s to %s' % (
            self.network, self.station, self.location, self.channel,
            len(self.timespans),
            format_time(self.timespans[0][0]) if self.timespans else '-',
            format_time(self.timespans[-1][1]) if self.timespans else '-'
        )

    def subtract(self, other):
        pass


class Retriever(SqliteSupport):

    def __init__(self, dbpath, temp_dir, availability, tolerance, log):
        super().__init__(dbpath, log)
        self._temp_dir = canonify(temp_dir)
        self._availability = availability
        self._tolerance = tolerance

    def retrieve(self, up):
        self._prepend_options(up)
        down = self._post_availability(up)
        try:
            self._sort_availability(down)
            for remote in self._parse_availability(down):
                print(remote)
                local = self._scan_index(remote.network, remote.station, remote.location, remote.channel)
                self._request_download(remote.subtract(local))
        finally:
            unlink(down)

    def _prepend_options(self, up):
        tmp = temp_path(self._temp_dir, up)
        self._log.debug('Prepending options to %s via %s' % (up, tmp))
        try:
            with open(tmp, 'w') as output:
                print('mergequality=true', file=output)
                print('mergesamplerate=true', file=output)
                with open(up, 'r') as input:
                    print(input.readline(), file=output, end='')
            unlink(up)
            copyfile(tmp, up)
        finally:
            unlink(tmp)

    def _post_availability(self, up):
        down = temp_path(self._temp_dir, up)
        return post_to_file(self._availability, up, down, self._log)

    def _sort_availability(self, down):
        tmp = temp_path(self._temp_dir, down)
        try:
            self._log.debug('Sorting %s via %s' % (down, tmp))
            run('sort %s > %s' % (down, tmp), self._log)  # todo - windows
            unlink(down)
            copyfile(tmp, down)
        finally:
            unlink(tmp)

    def _parse_line(self, line):
        n, s, l, c, b, e = line.split()
        return n, s, l, c, parse_time(b), parse_time(e)

    def _parse_availability(self, down):
        with open(down, 'r') as input:
            availability = None
            for line in input:
                if not line.startswith('#'):
                    n, s, l, c, b, e = self._parse_line(line)
                    if availability and not availability.is_sncl(n, s, l, c):
                        yield availability
                        availability = None
                    if not availability:
                        availability = Availability(self._tolerance, n, s, l, c)
                    availability.add_timespan(b, e)
            if availability:
                yield availability

    def _scan_index(self, network, station, location, channel):
        return None

    def _request_download(self, missing):
        return None  # todo - needs a download manager for chunking and buffering


def temp_path(temp_dir, text):
    name = uniqueish(RETRIEVEFILE, text)
    return unique_filename(join(temp_dir, name))


def assert_valid_time(time):
    if match(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?)?$', time):
        return time
    else:
        raise Exception('Invalid time format "%s"' % time)


def build_file(path, sncl, begin, end=None):
    parts = list(sncl.split('.'))
    if len(parts) != 4:
        raise Exception('SNCL "%s" does not have 4 components' % sncl)
    parts.append(assert_valid_time(begin))
    if end:
        parts.append(assert_valid_time(end))
    with open(path, 'w') as req:
       print(*parts, file=req)


def retrieve(args, log):
    temp_dir = canonify(args.temp_dir)
    makedirs(temp_dir, exist_ok=True)
    retriever = Retriever(args.mseed_db, temp_dir, args.availability_url, args.timespan_tol, log)
    if len(args.args) == 0 or len(args.args) > 3:
        raise Exception('Usage: rover %s (file|sncl begin [end])' % RETRIEVE)
    else:
        # guarantee always called with temp file because we prepend options
        path = temp_path(temp_dir, args.args[0])
        try:
            if len(args.args) == 1:
                copyfile(args.args[0], path)
            else:
                build_file(path, *args.args)
            retriever.retrieve(path)
        finally:
            unlink(path)
