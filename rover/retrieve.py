
from os import unlink
from os.path import join, exists
from re import match
from shutil import copyfile

from .utils import uniqueish, create_parents, canonify, post_to_file, unique_filename
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
        self._prepend_options(up)
        down = self._post_availability(up)
        try:
            self._sort_availability(down)
            for remote in self._parse_availability(down):
                local = self._scan_index(remote.network, remote.station, remote.location, remote.channel)
                self._request_download(remote.subtract(local))
        finally:
            unlink(down)

    def _prepend_options(self, up):
        pass

    def _post_availability(self, up):
        down = join(self._temp_dir, uniqueish(RETRIEVEFILE, up))
        return post_to_file(self._availability, up, down, self._log)

    def _sort_availability(self, down):
        pass

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
    retriever = Retriever(args.mseed_db, args.temp_dir, args.availability_url, log)
    if len(args.args) == 0 or len(args.args) > 3:
        raise Exception('Usage: rover %s (file|sncl begin [end])' % RETRIEVE)
    else:
        # guarantee always called with temp file because we prepend options
        name = uniqueish(RETRIEVEFILE, args.args[0])
        path = unique_filename(join(canonify(args.temp_dir), name))
        try:
            create_parents(path)
            if len(args.args) == 1:
                copyfile(args.args[0], path)
            else:
                build_file(path, *args.args)
            retriever.retrieve(path)
        finally:
            unlink(path)
