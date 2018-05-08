
from fnmatch import fnmatch
from os import listdir
from os.path import dirname, join
from re import sub
from tempfile import mktemp

import rover
from rover.args import Arguments, MSEEDDIR, MSEEDDB, TEMPDIR, LOGDIR, LEAP, MSEEDCMD
from rover.ingest import Ingester
from rover.logs import init_log
from rover.sqlite import init_db


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


class TestConfig:

    def __init__(self, dir, **kargs):
        kargs = dict(kargs)
        kargs[_(MSEEDDIR)] = join(dir, 'mseed')
        kargs[_(MSEEDDB)] = join(dir, 'index.sql')
        kargs[_(TEMPDIR)] = join(dir, 'tmp')
        kargs[_(LOGDIR)] = join(dir, 'logs')
        root = find_root()
        kargs[_(MSEEDCMD)] = join(root, '..', 'mseedindex', 'mseedindex')
        kargs[_(LEAP)] = False
        self.args = TestArgs(**kargs)
        self.log = init_log(self.args.log_dir, 7, 1, 5, 0, 'test', self.args.leap, 0)
        self.db = init_db(self.args.mseed_db, self.log)


def find_root():
    return dirname(dirname(rover.__file__))


def assert_files(dir, *files):
    found = listdir(dir)
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


