
from .utils import check_leap, check_cmd
from .scan import MseedFileScanner


class Indexer(MseedFileScanner):
    """
    Compare the filesystem and the database (using the iterators above)
    and when there is a discrepancy either add or remove an entry.
    """

    def __init__(self, config):
        super().__init__(config)
        args, log = config.args, config.log
        check_cmd('%s -h' % args.mseed_cmd, 'mseedindex', 'mseed-cmd', log)
        self._mseed_cmd = args.mseed_cmd
        self._mseed_db = args.mseed_db
        self._leap_file = check_leap(args.leap, args.leap_expire, args.leap_file, args.leap_url, log)
        self._dev = args.dev

    def _process(self, path):
        self._log.info('Indexing %s' % path)
        # todo - windows var
        self._workers.execute('LIBMSEED_LEAPSECOND_FILE=%s %s %s -sqlite %s %s'
                              % (self._leap_file, self._mseed_cmd, '-v -v' if self._dev else '', self._mseed_db, path))


def index(config):
    """
    Implement the index command.
    """
    # todo - check no args
    Indexer(config).run()
