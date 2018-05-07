
from argparse import ArgumentParser, Action, RawDescriptionHelpFormatter

from os.path import exists, join
from textwrap import dedent
import sys

from re import sub

from .utils import create_parents, canonify


COMPACT = 'compact'
COMPARE = 'compare'
DOWNLOAD = 'download'
HELP = 'help'
INDEX = 'index'
INGEST = 'ingest'
LIST_INDEX = 'list-index'
RESET_CONFIG = 'reset-config'
RETRIEVE = 'retrieve'
SUBSCRIBE = 'subscribe'

NO = '--no-'

ALL = 'all'
AVAILABILITYURL = 'availability-url'
COMPACTMUTATE = 'compact-mutate'
DAEMON = 'daemon'
DATASELECTURL = 'dataselect-url'
DELETEFILES = 'delete-files'
DELETETABLES = 'delete-tables'
DOWNLOADWORKERS = 'download-workers'
DEV = 'dev'
F, FILE = 'f', 'file'
HELP = 'help'
LEAP = 'leap'
LEAPEXPIRE = 'leap-expire'
LEAPFILE = 'leap-file'
LEAPURL = 'leap-url'
LOGDIR = 'log-dir'
LOGNAME = 'log-name'
LOGVERBOSITY = 'log-verbosity'
LOGSIZE = 'log-size'
LOGUNIQUE = 'log-unique'
LOGUNIQUEEXPIRE = 'log-unique-expire'
LOGCOUNT = 'log-count'
MSEEDCMD = 'mseed-cmd'
MSEEDDB = 'mseed-db'
MSEEDDIR = 'mseed-dir'
MSEEDWORKERS = 'mseed-workers'
MULTIPROCESS = 'multiprocess'
RECURSE = "recurse"
ROVERCMD = 'rover-cmd'
TEMPDIR = 'temp-dir'
TEMPEXPIRE = 'temp-expire'
TIMESPANTOL = 'timespan-tol'
V, VERBOSITY = 'v', 'verbosity'

DEFAULT_AVAILABILITYURL = 'http://service.iris.edu/irisws/availability/1/query'
DEFAULT_DATASELECTURL = 'http://service.iris.edu/fdsnws/dataselect/1/query'
DEFAULT_DOWNLOADWORKERS = 10
DEFAULT_FILE = join('~', 'rover', 'config')
DEFAULT_LEAPEXPIRE = 30
DEFAULT_LEAPFILE = join('~', 'rover', 'leap-seconds.lst')
DEFAULT_LEAPURL = 'http://www.ietf.org/timezones/data/leap-seconds.list'
DEFAULT_LOGDIR = join('~', 'rover', 'logs')
DEFAULT_LOGVERBOSITY = 5
DEFAULT_LOGSIZE = 6
DEFAULT_LOGCOUNT = 10
DEFAULT_LOGNAME = 'rover'
DEFAULT_LOGUNIQUE_EXPIRE = 7
DEFAULT_MSEEDCMD = 'mseedindex'
DEFAULT_MSEEDDB = join('~', 'rover', 'index.sql')
DEFAULT_MSEEDDIR = join('~', 'rover', 'mseed')
DEFAULT_MSEEDWORKERS = 10
DEFAULT_ROVERCMD = 'rover'
DEFAULT_TEMPDIR = join('~', 'rover', 'tmp')
DEFAULT_TEMPEXPIRE = 1
DEFAULT_TIMESPANTOL = 0.1
DEFAULT_VERBOSITY = 4


def parse_bool(value):
    '''
    Treat caseless true, yes and on and true, anything else as false.
    '''
    if not value:
        value = 'False'
    value = value.lower()
    return value in ('true', 'yes', 'on')


class StoreBoolAction(Action):

    '''
    We need a special action for booleans because we must covertly
    parse them as '--foo True' even though the user only types '--foo'.
    '''

    def __init__(self,
                 option_strings,
                 dest,
                 default=None,
                 choices=None,
                 required=False,
                 help=None,
                 metavar=None):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=1,
            const=None,
            default=default,
            type=parse_bool,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values[0])



def m(string): return '-' + string
def mm(string): return '--' + string


class Arguments(ArgumentParser):

    '''
    Extend the standard arg parsing to:
    * scan initial args to find if config file location specifed
    * if config file is missing, generate defaults
    * read config file before command line args

    To do this correctly for boolean flags (which behave differently on
    the command line and in the config file) we also have to
    pre-process those.

    The aim is to:
    * have (almost) all config duplcaited, both in config and command line
    * have default config be self-documenting and discoverable
    '''


    def __init__(self):
        super().__init__(fromfile_prefix_chars='@',
                         formatter_class=RawDescriptionHelpFormatter,
                         description='ROVER: Retrieval of Various Experiment data Robustly',
                         epilog=dedent('''
                         Flags can be negated (eg --no-daemon).
                         Defaults are read from the configuration file (%s).
                         Type "rover help" for more information on available commands.''' % DEFAULT_FILE))
        self.register('action', 'store_bool', StoreBoolAction)

        # operation details
        self.add_argument(m(F), mm(FILE), default=DEFAULT_FILE, help='specify configuration file')
        # metavar must be empty string to hide value since user options
        # are flags that are automatically given values below.
        self.add_argument(mm(DAEMON), default=False, action='store_bool', help='use background processes?', metavar='')
        self.add_argument(mm(DEV), default=False, action='store_bool', help='development mode (show exceptions)?', metavar='')
        self.add_argument(mm(DELETEFILES), default=True, action='store_bool', help='delete temporary files?', metavar='')
        self.add_argument(mm(DELETETABLES), default=True, action='store_bool', help='delete temporary database tables?', metavar='')

        # retrieval
        self.add_argument(mm(TIMESPANTOL), default=DEFAULT_TIMESPANTOL, action='store', help='tolerance for overlapping timespans', metavar='SECS', type=float)
        self.add_argument(mm(DOWNLOADWORKERS), default=DEFAULT_DOWNLOADWORKERS, action='store', help='number of download instances to run', metavar='N', type=int)
        self.add_argument(mm(MULTIPROCESS), default=False, action='store_bool', help='allow multiple processes (internal use only)?', metavar='')
        self.add_argument(mm(ROVERCMD), default=DEFAULT_ROVERCMD, action='store', help='command to run rover', metavar='CMD')

        # downloads
        self.add_argument(mm(AVAILABILITYURL), default=DEFAULT_AVAILABILITYURL, action='store', help='availability service url', metavar='DIR')
        self.add_argument(mm(DATASELECTURL), default=DEFAULT_DATASELECTURL, action='store', help='dataselect service url', metavar='DIR')
        self.add_argument(mm(TEMPDIR), default=DEFAULT_TEMPDIR, action='store', help='temporary storage for downloads', metavar='DIR')
        self.add_argument(mm(TEMPEXPIRE), default=DEFAULT_TEMPEXPIRE, action='store', help='number of days before deleting temp files', metavar='DAYS', type=int)

        # compact and index
        self.add_argument(mm(COMPACT), default=True, action='store_bool', help='call compact during ingest?', metavar='')
        self.add_argument(mm(COMPACTMUTATE), default=False, action='store_bool', help='allow compact to mutate data?', metavar='')
        self.add_argument(mm(ALL), default=False, action='store_bool', help='process all files (not just modified)?', metavar='')
        self.add_argument(mm(RECURSE), default=True, action='store_bool', help='when given a directory, process children?', metavar='')

        # logging
        self.add_argument(mm(LOGDIR), default=DEFAULT_LOGDIR, action='store', help='directory for logs', metavar='DIR')
        self.add_argument(mm(LOGNAME), default=DEFAULT_LOGNAME, action='store', help='base file name for logs', metavar='NAME')
        self.add_argument(mm(LOGUNIQUE), default=False, action='store_bool', help='unique log names (with PIDs)?', metavar='')
        self.add_argument(mm(LOGUNIQUEEXPIRE), default=DEFAULT_LOGUNIQUE_EXPIRE, action='store', help='number of days before deleting unique logs', metavar='DAYS', type=int)
        self.add_argument(mm(LOGVERBOSITY), default=DEFAULT_LOGVERBOSITY, action='store', help='log verbosity (0-5)', metavar='V', type=int)
        self.add_argument(mm(LOGSIZE), default=DEFAULT_LOGSIZE, action='store', help='maximum log size (1-10)', metavar='N', type=int)
        self.add_argument(mm(LOGCOUNT), default=DEFAULT_LOGCOUNT, action='store', help='maximum number of logs', metavar='N', type=int)
        self.add_argument(mm(VERBOSITY), default=DEFAULT_VERBOSITY, action='store', help='stdout verbosity (0-5)', metavar='V', type=int)

        # mseedindex
        self.add_argument(mm(MSEEDCMD), default=DEFAULT_MSEEDCMD, action='store', help='mseedindex command', metavar='CMD')
        self.add_argument(mm(MSEEDDB), default=DEFAULT_MSEEDDB, action='store', help='mseedindex database (also used by rover)', metavar='FILE')
        self.add_argument(mm(MSEEDDIR), default=DEFAULT_MSEEDDIR, action='store', help='root of mseed data dirs', metavar='DIR')
        self.add_argument(mm(MSEEDWORKERS), default=DEFAULT_MSEEDWORKERS, action='store', help='number of mseedindex instances to run', metavar='N', type=int)

        # leap seconds
        self.add_argument(mm(LEAP), default=True, action='store_bool', help='use leapseconds file?', metavar='')
        self.add_argument(mm(LEAPEXPIRE), default=DEFAULT_LEAPEXPIRE, action='store', help='number of days before refreshing file', metavar='N', type=int)
        self.add_argument(mm(LEAPFILE), default=DEFAULT_LEAPFILE, action='store', help='file for leapsecond data', metavar='FILE')
        self.add_argument(mm(LEAPURL), default=DEFAULT_LEAPURL, action='store', help='URL for leapsecond data', metavar='URL')

        # commands / args
        self.add_argument('command', metavar='COMMAND', nargs='?', help='use "help" for further information')
        self.add_argument('args', nargs='*', help='depends on the command - see above')

    def parse_args(self, args=None, namespace=None):
        '''
        Intercept normal arg parsing to:
        * scan initial args to find if config file location specified
        * if config file is missing, generate defaults
        * read config file before command line args
        '''
        if args is None:
            args = sys.argv[1:]
        args = self._preprocess_booleans(args)
        config, args = self._extract_config(args)
        self.write_config(config)
        args = self._patch_config(args, config)
        return super().parse_args(args=args, namespace=namespace)

    def _preprocess_booleans(self, args):
        '''
        Replace --foo with '--foo True' and --no-foo with '--foo False'.
        This makes the interface consistent with the config file (which has
        the format 'foo=True') while letting the user type simple flags.
        '''
        indices = []
        for (index, arg) in enumerate(args):
            if arg.startswith(NO):
                arg = '--' + arg[5:]
            for action in self._actions:
                name = '--' + sub('_', '-', action.dest)
                if name == arg and type(action) is StoreBoolAction:
                    indices.append(index)
        for index in reversed(indices):
            negative = args[index].startswith(NO)
            if negative:
                args[index] = mm(args[index][5:])
            args.insert(index+1, str(not negative))
        return args

    def _extract_config(self, args):
        '''
        Find the config file, if given, otherwise use the default.
        This must be done before argument parsing because we need
        to add the contents of the file to the arguments (that is
        how the file is read).
        '''
        config, indices = None, []
        # find all occurences of file params, saving last
        for (index, arg) in enumerate(args):
            # must skip file name
            if arg in ('-f', '--file') and (not indices or index+1 != indices[-1]):
                if index+1 >= len(args):
                    raise Exception('No argument for %s' % arg)
                indices.append(index)
                config = args[index+1]
        # remove all occurences
        for index in reversed(indices):
            args = args[:index] + args[index+2:]
        if not config:
            config = self.get_default(FILE)
        config = canonify(config)
        # include config flag so that it is set correctly, even if the extracted
        # value is the one that is used here
        return config, [mm(FILE), config] + args

    def write_config(self, path, values=None):
        '''
        If the config file is missing, fill it with default values.
        '''
        if not exists(path):
            create_parents(path)
            with open(path, 'w') as out:
                for action in self._actions:
                    if action.dest not in (HELP, FILE):
                        if action.default is not None:
                            if values:
                                value = getattr(values, action.dest)
                            else:
                                value = action.default
                            if action.help:
                                out.write('# %s\n' % action.help)
                            out.write('%s=%s\n' % (sub('_', '-', action.dest), value))
        return

    def _patch_config(self, args, config):
        '''
        Force the reading of the config file (ignored for update-config
        because we may be rewriting it because it has errors).
        '''
        if RESET_CONFIG in args:
            return args
        else:
            return ['@'+config] + args


    def convert_arg_line_to_args(self, arg_line):
        '''
        Parse a line from the config file, constructing '--name value" from name=value
        and ignoring comments.
        '''
        arg_line = arg_line.strip()
        if arg_line.startswith('#'):
            return []
        elif '=' in arg_line:
            name, value = arg_line.split('=', 1)
            return [mm(name), value]
        else:
            raise Exception('Cannot parse "%s"' % arg_line)


