
from .utils import canonify
from .index import Indexer
from .scan import ModifiedScanner, DirectoryScanner


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
            self._indexer.run(path)
        else:
            self._log.warn('Skipping index for file outside local store: %s' % path)

    def _compact(self, path):
        # todo - read
        index = 1
        data = None
        while index < len(data):
            lower, upper = self._signature(data, index), self._signature(data, index-1)
            if self._mergeable(lower, upper):
                self._merge(data, index)
                # follow merged block upwards unless at top
                index = max(1, index-1)
            elif lower < upper:
                self._swap(data, index)
                # follow merged block upwards unless at top
                index = max(1, index-1)
            else:
                index += 1

    def _signature(self, data, index):
        pass

    def _mergeable(selflower, upper):
        pass

    def _merge(self, data, index):
        pass

    def _swap(self, data, index):
        pass

