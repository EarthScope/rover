from os import makedirs
from re import compile, sub
from genericpath import exists, isfile
from os.path import basename, isabs, join, realpath, abspath, expanduser, dirname
from shutil import move

from .args import Arguments, LOGDIR, LOGSIZE, LOGCOUNT, LOGVERBOSITY, VERBOSITY, LOGNAME, LOGUNIQUE, LOGUNIQUEEXPIRE, \
    MSEEDDB
from .logs import init_log
from .sqlite import init_db
from .utils import safe_unlink

"""
Package common data used in all/most classes (db connection, lgs and parameters).
"""


class BaseConfig:

    def __init__(self, log, args, db, configdir):
        self.log = log
        self._args = args
        self.db = db
        self._configdir = configdir
        self.args = args.args
        self.command = args.command

    def arg(self, name, depth=0):
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

    def path(self, name):
        path = expanduser(self.arg(name))
        if not isabs(path):
            path = join(self._configdir, path)
        return realpath(abspath(path))

    def dir_path(self, name):
        path = self.path(name)
        if not exists(path):
            makedirs(path)
        return path

    def file_path(self, name):
        path = self.path(name)
        dir = dirname(path)
        if not exists(dir):
            makedirs(dir)
        return path


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
        super().__init__(None, args, None, configdir)
        self.log = init_log(self.dir_path(LOGDIR), self.arg(LOGSIZE), self.arg(LOGCOUNT), self.arg(LOGVERBOSITY),
                            self.arg(VERBOSITY), self.arg(LOGNAME), self.arg(LOGUNIQUE), self.arg(LOGUNIQUEEXPIRE))
        self.log.debug('Args: %s' % self._args)
        self.db = init_db(self.file_path(MSEEDDB), self.log)

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
