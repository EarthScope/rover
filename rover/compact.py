
from functools import total_ordering
from os import unlink
from os.path import basename, join
from shutil import move

from obspy import read
import numpy as np

from .utils import canonify, unique_filename, create_parents, format_epoch
from .index import Indexer
from .scan import ModifiedScanner, DirectoryScanner


@total_ordering
class Signature:
    """
    Encapsulate the metadata and associated logic for a trace / block.
    """

    def __init__(self, data, timespan_tol):
        self.net = data.stats.network
        self.sta = data.stats.station
        self.loc = data.stats.location
        self.cha = data.stats.channel
        self.qua = data.stats.mseed.dataquality
        self.sample_rate = data.stats.sampling_rate
        self.start_time = data.stats.starttime
        self.end_time = data.stats.endtime
        self.data_type = data.data.dtype
        self.n_samples = len(data.data)
        self._timespan_tol = timespan_tol

    def snclqr(self):
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
        return (type(other) == type(self) and self.snclqr() == other.snclqr() and
                ((self._before(other.start_time, self.end_time) and self._after(other.end_time, self.start_time)) or
                 (self._before(self.start_time, other.end_time) and self._after(self.end_time, other.start_time))))

    def __str__(self):
        return "%s.%s.%s.%s.%s (%gHz)" % (self.net, self.sta, self.loc, self.cha, self.qua, self.sample_rate)



class Compacter(ModifiedScanner, DirectoryScanner):
    """
    Compact modified files (remove redundant mseed data and tidy).

    We do this by bubble-sorting the data blocks, merging data when
    appropriate.  This allows us to replace data with the latest (later
    in the file) values.

    We also check whether duplciate data are mutated and raise an error
    if so (unless --compact-mutate is set).
    """

    def __init__(self, config):
        ModifiedScanner.__init__(self, config)
        DirectoryScanner.__init__(self, config)
        args = config.args
        self._mseed_dir = canonify(args.mseed_dir)
        self._temp_dir = canonify(args.temp_dir)
        self._timespan_tol = args.timespan_tol
        self._delete_files = args.delete_files
        self._compact_list = args.compact_list
        self._compact_mutate = args.compact_mutate
        self._compact_mixed_types = args.compact_mixed_types
        self._found_duplicates = False
        self._indexer = Indexer(config)

    def run(self, args):
        """
        Invoke the command over the appropriate files (See super classes)
        """
        if args:
            self.scan_dirs_and_files(args)
        else:
            self.scan_mseed_dir()

    def process(self, path):
        """
        Given a file, do the work and then index.
        """
        self._found_duplicates = False
        self._log.debug('Compacting %s' % path)
        mutated = self._compact(path)
        if path.startswith(self._mseed_dir):
            # do this even if file unchanged, as we may be part of pipeline
            self._indexer.run([path])
        else:
            self._log.warn('Skipping index for file outside local store: %s' % path)
        if self._found_duplicates:
            raise Exception('Some files in the store contain duplicate data')

    def _compact(self, path):
        """
        A modified (with merge) bubble sort.
        """
        data = read(path)
        index_lower, mutated = 1, False
        while index_lower < len(data):
            lower, upper = Signature(data[index_lower], self._timespan_tol), Signature(data[index_lower-1], self._timespan_tol)
            if lower.mergeable(upper):
                if self._compact_list:
                    if not self._found_duplicates:
                        self._log.warn('Found duplicate data; logging file paths to stdout and will raise error on completion')
                        self._found_duplicates = True
                    print(path)
                    return
                self._merge(data, index_lower, lower, upper)
                # follow merged block upwards unless at top
                index_lower = max(1, index_lower-1)
                mutated = True
            elif lower < upper:
                self._swap(data, index_lower)
                # follow bubbling swapped block upwards unless at the top
                index_lower = max(1, index_lower-1)
                mutated = True
            else:
                # nothing to do, so go down to the next bvlock
                index_lower += 1
        if mutated:
            self._replace(path, data)
        else:
            self._log.debug('File unchanged')
        return mutated

    def _replace(self, path, data):
        # do this carefully, so there's a backup if writing fails
        copy = unique_filename(join(self._temp_dir, basename(path)))
        self._log.debug('Moving old file to %s' % copy)
        create_parents(copy)
        move(path, copy)
        self._log.info('Writing compacted (%d traces) data to %s' % (len(data), path))
        for i in range(len(data)):
            self._log.debug(data[i])
        data.write(path, format='MSEED')
        if self._delete_files:
            self._log.debug('Deleting copy at %s' % copy)
            unlink(copy)

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

    def _append_snclqr(self, params, signature):
        return tuple(list(params) + list(signature.snclqr()))

    def _merge(self, data, index, lower, upper):
        self._log.info('Merging blocks %d and %d (%s.%s.%s.%s.%s %gHz)' % self._append_snclqr((index-1, index), lower))
        self._log.debug(' %s - %s / %s - %s' %
                        (format_epoch(upper.start_time), format_epoch(upper.end_time),
                         format_epoch(lower.start_time), format_epoch(lower.end_time)))
        # try to avoid harming data...
        if lower.data_type != upper.data_type:
            msg = 'Mixed data types: %s and %s (%s.%s.%s.%s.%s %gHz)' %\
                  self._append_snclqr((upper.data_type, lower.data_type), lower)
            if self._compact_mixed_types:
                self._log.warn(msg)
            else:
                raise Exception(msg)
        self._assert_size(upper.end_time - upper.start_time, upper.sample_rate, len(data[index-1].data))
        self._assert_size(lower.end_time - lower.start_time, lower.sample_rate, len(data[index].data))
        start_time = min(lower.start_time, upper.start_time)
        end_time = max(lower.end_time, upper.end_time)
        time_range = end_time - start_time
        n_samples = self._data_size(time_range, lower.sample_rate)
        new_data = np.empty((n_samples,), lower.data_type)
        # copy old data into new array, oldest first
        offset, length = self._locate(start_time, upper)
        new_data[offset:offset+length] = data[index-1].data
        offset, length = self._locate(start_time, lower)
        new_data[offset:offset+length] = data[index].data
        # then check oldest data was not modified
        offset, length = self._locate(start_time, upper)
        if not np.array_equal(new_data[offset:offset+length], data[index-1].data):
            msg = 'Modified data for %s.%s.%s.%s.% (%gHz) during merge' % lower.snclqr()
            if self._compact_mutate:
                self._log.warn(msg)
            else:
                raise Exception(msg)
        data[index-1].data = new_data
        # endtime is calculated from these
        data[index-1].stats.starttime = start_time
        data[index-1].stats.npts = n_samples
        data.remove(data[index])

    def _swap(self, data, index):
        self._log.info('Swapping blocks %d and %d' % (index-1, index))
        upper = data[index-1]
        data.remove(upper)
        data.insert(index, upper)


def compact(config):
    Compacter(config).run(config.args.args)
