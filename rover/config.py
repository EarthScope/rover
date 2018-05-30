from argparse import Namespace
from genericpath import exists, isfile
from os import makedirs
from os.path import basename, isabs, join, realpath, abspath, expanduser, dirname
from re import compile, sub
from shutil import move

from .args import Arguments, LOGDIR, LOGSIZE, LOGCOUNT, LOGVERBOSITY, VERBOSITY, LOGUNIQUE, LOGUNIQUEEXPIRE, \
    FILEVAR, HELP, DIRVAR, FILE, TEMPDIR, MSEEDDIR, COMMAND
from .logs import init_log
from .sqlite import init_db
from .utils import safe_unlink

"""
Package common data used in all/most classes (db connection, lgs and parameters).
"""


class BaseConfig:
    """
    The configuration of the system (log, parameters, database).

    The Config subclass provides a different constructor.
    """

    def __init__(self, log, log_path, args, db, configdir):
        self.log = log
        self.log_path = log_path
        self._args = args
        self.db = db
        self._configdir = configdir
        self.args = args.args
        self.command = args.command

    def arg(self, name, depth=0):
        """
        Look-up an arg with variable substitution.
        """
        name = sub('-', '_', name)
        if depth > 10:
            raise Exception('Circular definition involving %s' % name)
        try:
            value = getattr(self._args, name)
        except:
            raise Exception('Parameter %s does not exist' % name)
        while True:
            try:
                matchvar = compile(r'(.*(?:^|[^\$]))\${(\w+)}(.*)').match(value)
            except:
                # not a string variable
                break
            if matchvar:
                if matchvar.group(2) == 'CONFIGDIR':
                    inner = self._configdir
                else:
                    inner = self.arg(matchvar.group(2), depth=depth+1)
                try:
                    value = matchvar.group(1) + inner + matchvar.group(3)
                except:
                    print('oops')
                    raise Exception('String substitution only works with string parameters (%s)' % name)
            else:
                value = sub(r'\$\$', '$', value)
                break
        return value

    def absolute(self):
        """
        Clone this configuration, making file and directories absolute.  Used before we write a
        config for a sub-process, because it may be written in a different location to the original,
        so relative paths will change value (yeah that was a fun bug to fix).
        """
        args = {}
        for action in Arguments()._actions:
            name = action.dest
            if name not in (FILEVAR, HELP):
                if action.metavar in (DIRVAR, FILEVAR):
                    value = self.path(name)
                else:
                    value = self.arg(name)
                args[name] = value
        return BaseConfig(self.log, self.log_path, Namespace(**args), self.db, self._configdir)

    def path(self, name):
        """
        Paths have an implicit configdir if they are relative.
        """
        path = expanduser(self.arg(name))
        if not isabs(path):
            path = join(self._configdir, path)
        return realpath(abspath(path))

    def dir_path(self, name):
        """
        Ensure the directory exists.
        """
        path = self.path(name)
        if not exists(path):
            makedirs(path)
        return path

    def file_path(self, name):
        """
        Ensure the enclosing directory exists.
        """
        path = self.path(name)
        dir = dirname(path)
        if not exists(dir):
            makedirs(dir)
        return path


def mseed_db(config):
    return join(config.dir_path(MSEEDDIR), 'index.sql')


class Config(BaseConfig):
    """
    A container that encapsulates the core compoennts common to all commands.  Used to
    reduce the amount of argument passing and simplify chaining commands.
    """

    def __init__(self):
        argparse = Arguments()
        args, configdir = argparse.parse_args()
        # this is a bit ugly, but we need to use the base methods to construct the log and db
        # note that log is not used in base!
        super().__init__(None, None, args, None, configdir)
        self.log, self.log_path = \
            init_log(self.dir_path(LOGDIR), self.arg(LOGSIZE), self.arg(LOGCOUNT), self.arg(LOGVERBOSITY),
                     self.arg(VERBOSITY), self.arg(COMMAND) or 'rover', self.arg(LOGUNIQUE), self.arg(LOGUNIQUEEXPIRE))
        self.log.debug('Args: %s' % self._args)
        self.db = init_db(mseed_db(self), self.log)


class ConfigWriter:
    """
### Write Config

    rover write-config

Write default values to the config file.

##### Significant Parameters

@file
@verbosity
@log-dir
@log-verbosity

##### Examples

    rover write-config

will reset the configuraton in the default location.

    rover write-config -f ~/.roverrc

will write the config to the given file.

    """

    def __init__(self, config):
        self._log = config.log
        self._file = config.arg(FILE)
        self._args = config._args

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
        argparse.write_config(self._file, self._args)


def write_config(config, filename, **kargs):
    """
    Write a config file for sub-processes.
    """
    args = config.absolute()._args
    temp_dir = config.dir_path(TEMPDIR)
    config_path = join(temp_dir, filename)
    safe_unlink(config_path)
    Arguments().write_config(config_path, args, **kargs)
    return config_path
