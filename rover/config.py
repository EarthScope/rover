
from argparse import Namespace
from genericpath import exists
from os import makedirs
from os.path import isabs, join, realpath, abspath, expanduser, dirname
from re import compile, sub

from .args import Arguments, LOGDIR, LOGSIZE, LOGCOUNT, LOGVERBOSITY, VERBOSITY, LOGUNIQUE, LOGUNIQUEEXPIRE, \
    FILEVAR, DIRVAR, TEMPDIR, DATADIR, COMMAND, unbar, DYNAMIC_ARGS, INIT_REPOSITORY, m, F
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
            if unbar(name) not in DYNAMIC_ARGS:   # todo - should this include FILE?
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

    def dir(self, name):
        """
        Ensure the directory exists.
        """
        path = self.path(name)
        if not exists(path):
            makedirs(path)
        return path

    def file(self, name):
        """
        Ensure the enclosing directory exists.
        """
        path = self.path(name)
        dir = dirname(path)
        if not exists(dir):
            makedirs(dir)
        return path


def mseed_db(config):
    return join(config.dir(DATADIR), 'index.sql')


class Config(BaseConfig):
    """
    An alternative constructor for BaseConfig (bootstrap from command line).
    """

    def __init__(self):
        argparse = Arguments()
        args, self.__config = argparse.parse_args()
        self.__error = self.__config and not exists(self.__config)  # see logic in parse_args
        full_config = self.__config and not self.__error
        # this is a bit ugly, but we need to use the base methods to construct the log and db
        # note that log is not used in base!
        super().__init__(None, None, args, None, dirname(self.__config) if full_config else None)
        self.log, self.log_path = \
            init_log(self.dir(LOGDIR) if full_config else None, self.arg(LOGSIZE), self.arg(LOGCOUNT),
                     self.arg(LOGVERBOSITY), self.arg(VERBOSITY), self.arg(COMMAND) or 'rover',
                     self.arg(LOGUNIQUE), self.arg(LOGUNIQUEEXPIRE))
        if full_config:  # if initializing, we have no database...
            self.db = init_db(mseed_db(self), self.log)

    def lazy_validate(self):
        # allow Config() to be created so we can log on error
        if self.__error:
            self.log.error('Could not find %s' % self.__config)
            self.log.error('You may need to configure the local store using `rover %s %s %s`).' %
                           (INIT_REPOSITORY, m(F), self.__config))
            raise Exception('Could not find configuration file')


class RepoInitializer:
    """
### Initialise The Local Store

    rover init-repository [directory]

Creates the expected directory structure and writes default values to the
config file.

##### Significant Parameters

@verbosity
@log-dir
@log-verbosity

##### Examples

    rover init-repository

will create the local store in the current directory.

    rover init-repository ~/rover

will create the local store in ~/rover

    """

    def __init__(self, config):
        self._log = config.log
        self._args = config._args

    def run(self, args):
        """
        Implement the reset-config command - write the default parameters to the file
        given by -f (or default).
        """
        self.__validate()
        self.__check_target()
        self.__create()

    def __validate(self):
        pass

    def __check_target(self):
        pass

    def __create(self):
        pass


        # argparse = Arguments()
        # if exists(self._file):
        #     if not isfile(self._file):
        #         raise Exception('"%s" is not a file' % self._file)
        #     old = self._file + "~"
        #     if not exists(old) or isfile(old):
        #         self._log.info('Moving old config file to "%s"' % basename(old))
        #         safe_unlink(old)
        #         move(self._file, old)
        #     else:
        #         self._log.warn('Deleting %s' % self._file)
        #         safe_unlink(self._file)
        # self._log.info('Writing new config file "%s"' % self._file)
        # argparse.write_config(self._file, self._args)


def write_config(config, filename, **kargs):
    """
    Write a config file for sub-processes.
    """
    args = config.absolute()._args
    temp_dir = config.dir(TEMPDIR)
    config_path = join(temp_dir, filename)
    safe_unlink(config_path)
    Arguments().write_config(config_path, args, **kargs)
    return config_path
