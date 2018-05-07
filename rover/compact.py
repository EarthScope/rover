from _tracemalloc import start
from functools import total_ordering

from obspy import read
import numpy as np

from .utils import canonify
from .index import Indexer
from .scan import ModifiedScanner, DirectoryScanner


@total_ordering
class Signature:

    def __init__(self, data, index, timespan_tol):
        self.net = data[index].stats.network
        self.sta = data[index].stats.station
        self.loc = data[index].stats.location
        self.cha = data[index].stats.channel
        self.qua = data[index].stats.mseed.dataquality
        self.sample_rate = data[index].stats.sampling_rate
        self.start_time = data[index].stats.starttime
        self.end_time = data[index].stats.endtime
        self._timespan_tol = timespan_tol

    def _snclqr(self):
        return (self.net, self.sta, self.loc, self.cha, self.qua, self.sample_rate)

    def _tuple(self):
        return (self.net, self.sta, self.loc, self.cha, self.qua, self.sample_rate, self.start_time, self.end_time)

    def __eq__(self, other):
        return type(other) == type(self) and self._tuple() == other._tuple()

    def __lt__(self, other):
        return type(other) == type(self) and self._tuple() < other._tuple()

    def _before(self, a, b):
        return b - a > -self._timespan_tol

    def _after(self, a, b):
        return a - b > -self._timespan_tol

    def mergeable(self, other):
        return (type(other) == type(self) and self._snclqr() == other._snclqr() and
                ((self._before(other.start_time, self.end_time) and self._after(other.end_time, self.start_time)) or
                 (self._before(self.start_time, other.end_time) and self._after(self.end_time, other.start_time))))



class Compacter(ModifiedScanner, DirectoryScanner):
    """
    Compact modified files (remove redundant mseed data and tidy).

    We do this by bubble-sorting the data blocks, merging data when
    appropriate.  This allows us to replace data with the latest (later
    in the file) values.
    """

    def __init__(self, config):
        ModifiedScanner.__init__(self, config)
        DirectoryScanner.__init__(self, config)
        args = config.args
        self._mseed_dir = canonify(args.mseed_dir)
        self._timespan_tol = args.timespan_tol
        self._indexer = Indexer(config)

    def run(self, args):
        if args:
            self.scan_dirs_and_files(args)
        else:
            self.scan_mseed_dir()

    def process(self, path):
        self._log.info('Compacting %s' % path)
        self._compact(path)
        if path.startswith(self._mseed_dir):
            raise Exception('Stopping before index')
            self._indexer.run([path])
        else:
            self._log.warn('Skipping index for file outside local store: %s' % path)

    def _compact(self, path):
        data = read(path)
        index = 1
        while index < len(data):
            lower, upper = Signature(data, index, self._timespan_tol), Signature(data, index-1, self._timespan_tol)
            if lower.mergeable(upper):
                self._merge(data, index, lower, upper)
                # follow merged block upwards unless at top
                index = max(1, index-1)
            elif lower < upper:
                self._swap(data, index)
                # follow merged block upwards unless at top
                index = max(1, index-1)
            else:
                index += 1
        # todo write

    def _signature(self, data, index):
        return (data[index].stats.network, data[index].stats.station, data[index].stats.location,
                data[index].stats.channel, data[index].stats.sampling_rate,
                data[index].stats.starttime, data[index].stats.endtime)

    def _assert_int32(self, data):
        if data.dtype != np.int32:
            raise Exception("Unupported data type: %s" % data.dtype)

    def _data_size(self, secs, sample_rate):
        return int(1.5 + secs * sample_rate)

    def _assert_size(self, secs, sample_rate, n):
        if self._data_size(secs, sample_rate) != n:
            raise Exception('Unexpected data size: %d values for %fs at %fHz' % (n, secs, sample_rate))

    def _offset(self, zero, start_time, sample_rate):
        return int(0.5 + (start_time - zero) * sample_rate)

    def _locate(self, zero, signature):
        offset = self._offset(zero, signature.start_time, signature.sample_rate)
        length = self._data_size(signature.end_time - signature.start_time, signature.sample_rate)
        return offset, length

    def _merge(self, data, index, lower, upper):
        self._log.debug('merge %d' % index)
        self._assert_int32(data[index-1].data)
        self._assert_int32(data[index].data)
        self._assert_size(upper.end_time - upper.start_time, upper.sample_rate, len(data[index-1].data))
        self._assert_size(lower.end_time - lower.start_time, lower.sample_rate, len(data[index].data))
        start_time = min(lower.start_time, upper.start_time)
        end_time = max(lower.end_time, upper.end_time)
        time_range = end_time - start_time
        n_samples = self._data_size(time_range, lower.sample_rate)
        new_data = np.empty((n_samples,), np.int32)
        # copy old data into new array, oldest first
        offset, length = self._locate(start_time, upper)
        new_data[offset:offset+length] = data[index-1].data
        offset, length = self._locate(start_time, lower)
        new_data[offset:offset+length] = data[index].data
        # then check oldest data was not modified
        offset, length = self._locate(start_time, upper)
        # todo - allow via flag
        if not np.array_equal(new_data[offset:offset+length], data[index-1].data):
            raise Exception('Modified data during merge')
        data[index-1].data = new_data
        data[index-1].stats.starttime = start_time
        data[index-1].stats.npts = len(new_data)
        data.remove(data[index])

    def _swap(self, data, index):
        self._log.debug('swap %d' % index)
        upper = data[index-1]
        data.remove(upper)
        data.insert(index, upper)


def compact(config):
    Compacter(config).run(config.args.args)
