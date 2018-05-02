
from os import unlink
from os.path import join, exists
from re import match

from .utils import uniqueish, create_parents, canonify, post_to_file
from .config import RETRIEVE
from .sqlite import SqliteSupport


RETRIEVEFILE = 'rover_retrieve'


class Availability:  # todo - more general name

    def __init__(self, network, station, location, channel):
        self.network = network
        self.station = station
        self.location = location
        self.channel = channel
        self.timespans = []

    def add_timespan(self, begin, end):
        # todo - something clever here
        pass

    def subtract(self, other):
        pass


class Retriever(SqliteSupport):

    def __init__(self, dbpath, temp_dir, availability, log):
        super().__init__(dbpath, log)
        self._temp_dir = canonify(temp_dir)
        self._availability = availability

    def retrieve(self, up):
        up = canonify(up)
        if not exists(up):
            raise Exception('Cannot find file %s' % up)
        down = self._get_availability(up)
        try:
            for remote in self._parse_availability(down):
                local = self._scan_index(remote.network, remote.station, remote.location, remote.channel)
                self._request_download(remote.subtract(local))
        finally:
            unlink(down)

    def _get_availability(self, up):
        down = join(self._temp_dir, uniqueish(RETRIEVEFILE, up))
        return post_to_file(self._availability, up, down, self._log)

    def _parse_availability(self, down):
        yield None

    def _scan_index(self, network, station, location, channel):
        return None

    def _request_download(self, missing):
        return None  # todo - needs a download manager for chunking and buffering


def assert_valid_time(time):
    if match(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?)?$', time):
        return time
    else:
        raise Exception('Invalid time format "%s"' % time)


def build_file(temp_dir, sncl, begin, end=None):
    parts = list(sncl.split('.'))
    if len(parts) != 4:
        raise Exception('SNCL "%s" does not have 4 components' % sncl)
    parts.append(assert_valid_time(begin))
    if end:
        parts.append(assert_valid_time(end))
    name = uniqueish(RETRIEVEFILE, sncl)
    path = join(canonify(temp_dir), name)
    create_parents(path)
    with open(path, 'w') as req:
       print(*parts, file=req)
    return path


def retrieve(args, log):
    retriever = Retriever(args.mseed_db, args.temp_dir, args.availability_url, log)
    if len(args.args) == 1:
        retriever.retrieve(args.args[0])
    elif len(args.args) == 0 or len(args.args) > 3:
        raise Exception('Usage: rover %s (file|sncl begin [end])' % RETRIEVE)
    else:
        path = build_file(args.temp_dir, *args.args)
        try:
            retriever.retrieve(path)
        finally:
            unlink(path)


