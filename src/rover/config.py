
from argparse import Namespace
from genericpath import exists
from os import makedirs, getcwd
from os.path import isabs, join, realpath, abspath, expanduser, dirname
from re import compile, sub

from .args import Arguments, LOGDIR, LOGSIZE, LOGCOUNT, LOGVERBOSITY, \
    VERBOSITY, LOGUNIQUE, LOGUNIQUEEXPIRE, FILEVAR, DIRVAR, TEMPDIR, DATADIR, \
    COMMAND, unbar, DYNAMIC_ARGS, INIT_REPOSITORY, m, F, FILE, FULLCONFIG, ASDF_FILENAME
from .logs import init_log, log_name
from .sqlite import init_db
from .utils import safe_unlink, canonify

"""
Package common data used in all/most classes (db connection, logs and options).
"""


class BaseConfig:
    """
    The configuration of the system (log, options, database).

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
        # make arguments absolute
        self.set_args_absolute()

    def set_args_absolute(self):
        """
        Make file and directories have absolute paths
        """
        abs_args = {}
        for action in Arguments()._actions:
            name = action.dest
            if unbar(name) not in DYNAMIC_ARGS:
                if action.metavar in (DIRVAR, FILEVAR):
                    value = self.path(name)
                else:
                    value = self.arg(name)
                abs_args[name] = value
        abs_args = Namespace(**abs_args)
        self._args = abs_args
        self.args = abs_args.args

    def set_configdir(self, configdir):
        """
        Called only from initialisation, when using a new config dir.
        """
        self._configdir = configdir

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
            raise Exception('Option %s does not exist' % name)
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

    def path(self, name):
        """
        Paths have an implicit configdir if they are relative.
        """
        path = expanduser(self.arg(name))
        if self._configdir and not isabs(path):
            path = join(self._configdir, path)
        return realpath(abspath(path))

    def dir(self, name, create_dir=True):
        """
        Ensure the directory exists.
        """
        path = self.path(name)
        if create_dir and not exists(path):
            makedirs(path)
        return path

    def file(self, name, create_dir=True):
        """
        Ensure the enclosing directory exists.
        """
        path = self.path(name)
        dir = dirname(path)
        if create_dir and not exists(dir):
            makedirs(dir)
        return path

    def dump_log(self):
        """Only for tests"""
        pass


def timeseries_db(config):
    return join(config.dir(DATADIR), 'timeseries.sqlite')

def asdf_container(config):
    return join(config.dir(DATADIR), config.arg(ASDF_FILENAME))


class Config(BaseConfig):
    """
    An alternative constructor for BaseConfig (bootstrap from command line).
    """

    def __init__(self):
        argparse = Arguments()
        args, self.__config = argparse.parse_args()

        # there's a pile of ugliness here so that we delay error handling until we have logs.
        # see also comments in parse_args.
        self.__error = self.__config and not exists(self.__config)  # see logic in parse_args
        full_config = self.__config and not self.__error

        # Special case of initializing repository, set config directory
        configdir = None
        if args.command and args.command in (INIT_REPOSITORY):
            if not args.args:
                configdir = getcwd()
            elif len(args.args) == 1:
                configdir = args.args[0]
            else:
                raise Exception('Command %s takes at most one argument - the directory to initialise' %
                                INIT_REPOSITORY)
            configdir = canonify(configdir)

        # this is a bit ugly, but we need to use the base methods to construct the log and db
        # note that log is not used in base!
        super().__init__(None, None, args, None, dirname(self.__config) if full_config else configdir)
        self.log, self.log_path, self.__log_stream = \
            init_log(self.dir(LOGDIR) if full_config else None, self.arg(LOGSIZE), self.arg(LOGCOUNT),
                     self.arg(LOGVERBOSITY), self.arg(VERBOSITY), self.arg(COMMAND) or 'rover',
                     self.arg(LOGUNIQUE), self.arg(LOGUNIQUEEXPIRE))
        if full_config:  # if initializing, we have no database...
            self.db = init_db(timeseries_db(self), self.log)

    def lazy_validate(self):
        # allow Config() to be created first so we can log on error (see main()),
        if self.__error:
            self.log.error('You may need to configure the repository using `rover %s %s %s`).' %
                           (INIT_REPOSITORY, m(F), self.__config))
            raise Exception('Could not find configuration file (%s)' % self.__config)

    def dump_log(self):
        """
        Called only from initialization, when logging to an in-memory stream.
        """
        path, dir = log_name(self.dir(LOGDIR), self.arg(COMMAND))
        self.log.info('Dumping log to %s' % path)
        with open(path, 'w') as out:
            out.write(self.__log_stream.getvalue())


class RepoInitializer:
    """
### Init Repository

    rover init-repository [directory]

    rover init-repo [directory]

    rover init [directory]

Initializes a given directory, or the current directory if no argument is
provided, as a ROVER data repository. Init repository will create a
configuration file, rover.config, as well as log and data directories.

   The aliases `rover init-repo` and `rover int` also exist.

To avoid over-writing data, rover init-repo returns an error if
a rover.config file, data or log directory exist in the targeted directory.

##### Significant Options

@verbosity
@log-dir
@log-verbosity

##### Examples

    rover init-repository

will create the repository in the current directory.

    rover init-repository ~/rover

will create the repository in ~/rover

    """

    def __init__(self, config):
        self.__config = config
        self.__log = config.log
        self.__args = config._args

    def run(self, args):
        self.__check_empty()
        self.__create()

    def __check_empty(self):
        data_dir = self.__config.dir(DATADIR, create_dir=False)
        if exists(data_dir):
            raise Exception('The data directory already exists (%s)' % data_dir)
        config_file = self.__config.file(FILE, create_dir=False)
        if exists(config_file):
            raise Exception('The configuration file already exists (%s)' % config_file)
        log_dir = self.__config.dir(LOGDIR, create_dir=False)
        if exists(log_dir):
            raise Exception('The log directory already exists (%s)' % log_dir)
        # no need to check database because that's inside the data dir

    def __create(self):
        config_file = self.__config.file(FILE)
        self.__log.default('Writing new config file "%s"' % config_file)
        Arguments().write_config(config_file, self.__args, WRITE_FULL_CONFIG=self.__config.arg(FULLCONFIG))
        self.__config.dir(DATADIR)
        db = init_db(timeseries_db(self.__config), self.__log)
        db.execute('PRAGMA journal_mode=WAL')
        self.__config.dump_log()


def write_config(config, filename, **kargs):
    """
    Write a config file for sub-processes.
    """
    args = config._args
    temp_dir = config.dir(TEMPDIR)
    config_path = join(temp_dir, filename)
    safe_unlink(config_path)
    Arguments().write_config(config_path, args, **kargs)
    return config_path
