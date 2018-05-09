
from .workers import Workers, SingleSNCLDayWorkers
from .utils import check_leap, check_cmd
from .scan import ModifiedScanner, DirectoryScanner


class Indexer(ModifiedScanner, DirectoryScanner):
    """
    Run mssedindex on modified files (and delete entries for missing files).
    """

    def __init__(self, config):
        ModifiedScanner.__init__(self, config)
        DirectoryScanner.__init__(self, config)
        args, log = config.args, config.log
        check_cmd('%s -h' % args.mseed_cmd, 'mseedindex', 'mseed-cmd', log)
        self._mseed_cmd = args.mseed_cmd
        self._mseed_db = args.mseed_db
        self._leap_file = check_leap(args.leap, args.leap_expire, args.leap_file, args.leap_url, log)
        self._dev = args.dev
        self._workers = SingleSNCLDayWorkers(config, args.mseed_workers)

    def run(self, args):
        if not args:
            self._log.info('Indexing all changed files')
            self.scan_mseed_dir()
        else:
            self.scan_dirs_and_files(args)

    def process(self, path):
        self._log.info('Indexing %s' % path)
        # todo - windows var
        self._workers.execute_with_lock('LIBMSEED_LEAPSECOND_FILE=%s %s %s -sqlite %s %s'
                                        % (self._leap_file, self._mseed_cmd, '-v -v' if self._dev else '', self._mseed_db, path),
                                        path)

    def done(self):
        self._workers.wait_for_all()


def index(config):
    """
    Implement the index command.
    """
    Indexer(config).run(config.args.args)
