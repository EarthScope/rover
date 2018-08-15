
from fnmatch import fnmatch
from getpass import getuser
from os import listdir, makedirs
from os.path import dirname, join, exists
from random import randint
from re import sub
from shutil import rmtree
from time import time

import rover
from rover.config import BaseConfig
from rover.args import Arguments, DATADIR, TEMPDIR, LOGDIR, LEAP, MSEEDINDEXCMD
from rover.ingest import Ingester
from rover.logs import init_log
from rover.sqlite import init_db
from rover.utils import create_parents, canonify, windows


class TestArgs:

    def __init__(self, **kargs):
        self._kargs = kargs
        self._argparser = Arguments()

    def __getattr__(self, item):
        if item in self._kargs:
            value = self._kargs[item]
        else:
            value = self._argparser.get_default(item)
        return value


def _(text):
    return sub(r'\-', '_', text)


class TestConfig(BaseConfig):

    def __init__(self, dir, **kargs):
        kargs = dict(kargs)
        kargs[_(DATADIR)] = join(dir, 'data')
        kargs[_(TEMPDIR)] = join(dir, 'tmp')
        kargs[_(LOGDIR)] = join(dir, 'logs')
        root = find_root()
        kargs[_(MSEEDINDEXCMD)] = join(root, '..', 'mseedindex', 'mseedindex')
        kargs[_(LEAP)] = False
        args = TestArgs(**kargs)
        self.command = args.command
        log, log_path, log_stream = init_log(args.log_dir, 7, 1, 5, 0, 'test', args.leap, 0)
        dbpath = join(canonify(args.data_dir), 'timeseries.sqlite')
        create_parents(dbpath)
        super().__init__(log, log_path, args, init_db(dbpath, log), dir)


def find_root():
    return dirname(dirname(rover.__file__))


def assert_files(dir, *files):
    found = listdir(dir)
    if 'timeseries.sqlite' in found:
        found.remove('timeseries.sqlite')
    assert len(files) == len(found), 'Found %d files in %s (not %d)' % (len(found), dir, len(files))
    for file in found:
        ok = False
        for glob in files:
            if fnmatch(file, glob):
                ok = True
        if not ok:
            raise Exception('Unexpected file: "%s"', file)


def ingest_and_index(dir, data, **opts):
    config = TestConfig(dir, **opts)
    ingester = Ingester(config)
    ingester.run(data)
    return config


class WindowsTemp:
    """
    An ugly hack to work around problems with TemporaryDir on windows.
    """

    def __init__(self, context, cleanup=True):
        self._context = context
        self._cleanup = cleanup
        self._dir = "C:\\Users\\%s\\AppData\\Local\\Temp\\rover\\%d-%s" % (getuser(), time(), randint(1000, 9999))

    def __enter__(self):
        if windows():
            if not exists(self._dir):
                makedirs(self._dir)
            return self._dir
        else:
            self._context = self._context()
            return self._context.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if windows():
            if self._cleanup:
                rmtree(self._dir, ignore_errors=True)
        else:
            return self._context.__exit__(exc_type, exc_val, exc_tb)
