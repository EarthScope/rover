
from fnmatch import fnmatch
from os import listdir, X_OK
from os.path import dirname, join
from re import sub
from shutil import which

import rover
from rover.config import BaseConfig
from rover.args import Arguments, DATADIR, TEMPDIR, LOGDIR, MSEEDINDEXCMD
from rover.ingest import Ingester
from rover.logs import init_log
from rover.sqlite import init_db
from rover.utils import create_parents, canonify


class TestArgs:
    __test__ = False
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
    __test__ = False
    def __init__(self, dir, **kargs):
        kargs = dict(kargs)
        kargs[_(DATADIR)] = join(dir, 'data')
        kargs[_(TEMPDIR)] = join(dir, 'tmp')
        kargs[_(LOGDIR)] = join(dir, 'logs')
        kargs[_(MSEEDINDEXCMD)] = which('mseedindex', mode=X_OK)
        args = TestArgs(**kargs)
        self.command = args.command
        log, log_path, log_stream = init_log(args.log_dir, '7M', 1, 5, 0, 'test', None, 0)
        dbpath = join(canonify(args.data_dir), 'timeseries.sqlite')
        create_parents(dbpath)
        super().__init__(log, log_path, args, init_db(dbpath, log), dir)


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

