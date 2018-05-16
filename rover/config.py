
from genericpath import exists, isfile
from os.path import basename
from shutil import move

from .args import Arguments
from .logs import init_log
from .sqlite import init_db
from .utils import safe_unlink

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


class ConfigResetter:
    """
### Reset Config

    rover reset-config

Write default values to the config file.

##### Significant Parameters

@file
@verbosity
@log-dir
@log-name
@log-verbosity

##### Examples

    rover reset-config

will reset the configuraton in the default location.

    rover reset-config -f ~/.roverrc

will write the config to the given file.

    """

    def __init__(self, config):
        self._log = config.log
        self._file = config.args.file

    def run(self, args):
        """
        Implement the reset-config command - write the default parameters to the file
        given by -f (or default).
        """
        argparse = Arguments()
        if exists(self._file):
            if not isfile(self._file):
                raise Exception('"%s" is not a file' % self._file)
            old = self._file + "~"
            if not exists(old) or isfile(old):
                self._log.info('Moving old config file to "%s"' % basename(old))
                safe_unlink(old)
                move(self._file, old)
            else:
                self._log.warn('Deleting %s' % self._file)
                safe_unlink(self._file)
        self._log.info('Writing new config file "%s"' % self._file)
        argparse.write_config(self._file)
