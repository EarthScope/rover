
from .args import MSEEDCMD, MSEEDDB, LEAP, LEAPEXPIRE, LEAPFILE, LEAPURL, DEV, VERBOSITY, MSEEDWORKERS
from .lock import MSEED
from .scan import ModifiedScanner, DirectoryScanner
from .utils import check_leap, check_cmd, canonify
from .workers import NoConflictPerDatabaseWorkers


"""
The 'rover index' command - call mseeedindex to update the tsindex table.
"""


class Indexer(ModifiedScanner, DirectoryScanner):
    """
### Index

    rover index [--all]

    rover index (file|dir)+

Index the files (add or change entires in the tsindex table in the mseed database).

When no argument is give all modified files in the local store are processed.  To force all files, use `--all`.

When a directory is given, all files contained in that directory are processed, along with the contents of
sub-directories, unless `--no-recurse` is specified.

The `mseedindex` command is used to index the data.  This optionally uses a file of leap-second data.  By default
(unless `--no-leap`) a file is downloaded from `--leap-url` if the file currently at `--leap-file` is missing or older
than `--leap-expire` days.

##### Significant Parameters

@all
@mseed-cmd
@mseed-dir
@mseed-db
@mseed-workers
@leap
@leap-expire
@leap-file
@leap-url
@verbosity
@log-dir
@log-name
@log-verbosity

##### Examples

    rover index --all

will index the entire store.

"""

# Most of the work is done in the scanner superclasses which find the files
# to modify, and in the worker that runs mseedindex.

    def __init__(self, config):
        ModifiedScanner.__init__(self, config)
        DirectoryScanner.__init__(self, config)
        self._mseed_cmd = check_cmd(config.arg(MSEEDCMD), 'mseedindex', 'mseed-cmd', config.log)
        self._mseed_db = config.file_path(MSEEDDB)
        self._leap_file = check_leap(config.arg(LEAP), config.arg(LEAPEXPIRE), config.arg(LEAPFILE), config.arg(LEAPURL), config.log)
        self._verbose = config.arg(DEV) and config.arg(VERBOSITY) == 5
        self._workers = NoConflictPerDatabaseWorkers(config, config.arg(MSEEDWORKERS), MSEED)

    def run(self, args):
        """
        Find the files to process (see superclasses).
        """
        if not args:
            self._log.info('Indexing all changed files')
            self.scan_mseed_dir()
        else:
            self.scan_dirs_and_files(args)

    def process(self, path):
        """
        Run mseedindex asynchronously in a worker.
        """
        self._log.info('Indexing %s' % path)
        # todo - windows var
        self._workers.execute_with_lock('LIBMSEED_LEAPSECOND_FILE=%s %s %s -sqlite %s %s'
                                        % (self._leap_file, self._mseed_cmd, '-v -v' if self._verbose  else '',
                                           self._mseed_db, path),
                                        path)

    def done(self):
        self._workers.wait_for_all()
