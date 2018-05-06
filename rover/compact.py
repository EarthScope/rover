
from .scan import MseedFileScanner


class Compac(MseedFileScanner):
    """
    Compact modified files (remove redundant mseed data and tidy).
    """

    def __init__(self, config):
        super().__init__(config)

    def _process(self, path):
        self._log.info('Compacting %s' % path)
