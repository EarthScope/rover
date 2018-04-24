
from os import listdir
from os.path import exists, isdir, join, isfile

from .utils import canonify, run, check_cmd
from .sqlite import Sqlite


class Ingester(Sqlite):
    """
    Run mseed index on the given files / dirs, copy them
    into the local store, and index them.
    """

    def __init__(self, mseedindex, dbpath, root, log):
        dbpath = canonify(dbpath)
        super().__init__(dbpath, log)
        check_cmd('%s -h' % mseedindex, 'mseedindex', 'mseed-cmd', log)
        self._mseedindex = mseedindex
        self._dbpath = dbpath
        self._root = canonify(root)

    def ingest(self, args):
        for arg in args:
            arg = canonify(arg)
            if not exists(arg):
                raise Exception('Cannot find %s' % arg)
            if isdir(arg):
                self._ingest_dir(arg)
            else:
                self._ingest_file(arg)

    def _ingest_dir(self, dir):
        for file in listdir(dir):
            path = join(dir, file)
            if isfile(path):
                self._ingest_file(path)
            else:
                self._log.warn('Ignoring %s in %s (not a file)' % (file, dir))

    def _ingest_file(self, file):
        self._execute('drop table if exists rover_import')
        self._log.info('Examining %s' % file)
        run('%s -table rover_import -sqlite %s %s' % (self._mseedindex, self._dbpath, file), self._log)


def ingest(args, log):
    ingester = Ingester(args.mseed_cmd, args.mseed_db, args.mseed_dir, log)
    ingester.ingest(args.args)
