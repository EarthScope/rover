
from genericpath import exists, isfile
from os import unlink
from os.path import basename
from shutil import move

from .args import Arguments
from .logs import init_log
from .sqlite import init_db


"""
Package common data used in all/most classes (db connection, lgs and parameters).
"""


class Config:
    """
    A container that encapsulates the core compoennts common to all commands.  Used to
    reduce the amount of argument passing and simplify chaining commands.
    """

    def __init__(self):
        argparse = Arguments()
        self.args = argparse.parse_args()
        self.log = init_log(self.args.log_dir, self.args.log_size, self.args.log_count, self.args.log_verbosity,
                            self.args.verbosity, self. args.log_name, self.args.log_unique, self.args.log_unique_expire)
        self.log.debug('Args: %s' % self.args)
        self.db = init_db(self.args.mseed_db, self.log)


class ArgsProxy:
    """
    A wrapper that allows new values to override existing arguments.
    """

    def __init__(self, args, kargs):
        self._args = args
        self._kargs = kargs

    def __getattr__(self, item):
        if item.startswith('_'):
            return super().__getattribute__(item)
        elif item in self._kargs:
            return self._kargs[item]
        else:
            return getattr(self._args, item)


class NewConfig:
    """
    Add new arguments (parameters) to an existing Config.
    """

    def __init__(self, config, **kargs):
        self.args = ArgsProxy(config.args, kargs)
        self.log = config.log
        self.db = config.db


def reset_config(config):
    """
    Implement the reset-config command - write the default parameters to the file
    given by -f (or default).
    """
    argparse = Arguments()
    file, log = config.args.file, config.log
    if exists(file):
        if not isfile(file):
            raise Exception('"%s" is not a file' % file)
        old = file + "~"
        if not exists(old) or isfile(old):
            log.info('Moving old config file to "%s"' % basename(old))
            if exists(old): unlink(old)
            move(file, old)
        else:
            log.warn('Deleting %s' % file)
            unlink(file)
    log.info('Writing new config file "%s"' % file)
    argparse.write_config(file)
