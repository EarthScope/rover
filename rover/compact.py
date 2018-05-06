
from .index import Indexer
from .scan import Scanner


class Compacter(Scanner):
    """
    Compact modified files (remove redundant mseed data and tidy).

    We do this by bubble-sorting the data blocks, merging data when
    appropriate.  This allows us to replace data with the latest (later
    in the file) values.
    """

    def __init__(self, config):
        super().__init__(config)
        self._indexer = Indexer(config)

    def process(self, path):
        self._log.info('Compacting %s' % path)
        # todo - read
        index = 1
        data = None
        while index < len(data):
            lower, upper = self._signature(data, index), self._signature(data, index-1)
            if self._meregable(lower, upper):
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

    def done(self):
        self._indexer.run()
