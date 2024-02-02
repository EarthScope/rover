
import sys
from argparse import ArgumentParser, Action, RawDescriptionHelpFormatter, SUPPRESS
from os.path import exists, join
from re import sub
from smtplib import SMTP_PORT
from textwrap import dedent

from .__version__ import __version__
from .utils import create_parents, canonify, check_cmd, dictionary_text_list

"""
Command line / file configuration parameters.
"""

ERROR_CODE = 1
ABORT_CODE = 2

# commands
DAEMON = 'daemon'
DOWNLOAD = 'download'
HELP_CMD = 'help'
INDEX = 'index'
INGEST = 'ingest'
LIST_INDEX = 'list-index'
LIST_RETRIEVE = 'list-retrieve'
LIST_SUBSCRIBE = 'list-subscribe'
LIST_SUMMARY = 'list-summary'
RETRIEVE = 'retrieve'
RETRIEVE_METADATA = 'retrieve-metadata'
START = 'start'
STOP = 'stop'
STATUS = 'status'
SUMMARY = 'summary'
SUBSCRIBE = 'subscribe'
TRIGGER = 'trigger'
UNSUBSCRIBE = 'unsubscribe'
WEB = 'web'
INIT = 'init'
INIT_REPO = 'init-repo'
INIT_REPOSITORY = 'init-repository'


# flag negation
NO = '--no-'


# parameters
ALL = 'all'
ARGS = 'args'
ASDF_FILENAME = 'asdf-filename'
AVAILABILITYURL = 'availability-url'
COMMAND = 'command'
DATADIR = 'data-dir'
DATASELECTURL = 'dataselect-url'
DELETEFILES = 'delete-files'
DOWNLOADRETRIES = 'download-retries'
DOWNLOADWORKERS = 'download-workers'
DEV = 'dev'
EMAIL = 'email'
EMAILFROM = 'email-from'
F, FILE = 'f', 'file'
FORCECMD = 'force-cmd'
FORCEFAILURES = 'force-failures'
FORCE_METADATA_RELOAD = 'force-metadata-reload'
FORCEREQUEST = 'force-request'
H, FULLHELP = 'H', 'full-help'
_h, _help = 'h', 'help'
FULLCONFIG = 'full-config'
HTTPBINDADDRESS = 'http-bind-address'
HTTPPORT = 'http-port'
HTTPRETRIES = 'http-retries'
HTTPTIMEOUT = 'http-timeout'
LOGDIR = 'log-dir'
LOGVERBOSITY = 'log-verbosity'
LOGSIZE = 'log-size'
LOGUNIQUE = 'log-unique'
LOGUNIQUEEXPIRE = 'log-unique-expire'
LOGCOUNT = 'log-count'
MDFORMAT = 'md-format'
MSEEDINDEXCMD = 'mseedindex-cmd'
MSEEDINDEXWORKERS = 'mseedindex-workers'
OUTPUT_FORMAT = 'output-format'
POSTSUMMARY = 'post-summary'
PREINDEX = 'pre-index'
RECHECKPERIOD = 'recheck-period'
RECURSE = "recurse"
ROVERCMD = 'rover-cmd'
SMTPADDRESS = 'smtp-address'
SMTPPORT = 'smtp-port'
SORTINPYTHON = 'sort-in-python'
STATIONURL = 'station-url'
SUBSCRIPTIONSDIR = 'subscriptions-dir'
TEMPDIR = 'temp-dir'
TEMPEXPIRE = 'temp-expire'
TIMESPANINC = 'timespan-inc'
TIMESPANTOL = 'timespan-tol'
LITTLE_V, VERBOSITY = 'v', 'verbosity'
BIG_V, VERSION = 'V', 'version'

LITTLE_HELP = (DOWNLOADRETRIES, LOGDIR, VERBOSITY, EMAIL,
               VERSION, HELP_CMD, FULLHELP, FILE, AVAILABILITYURL, DATASELECTURL)
LITTLE_CONFIG = (DATADIR, DOWNLOADRETRIES, DOWNLOADWORKERS, OUTPUT_FORMAT,
                 ASDF_FILENAME, STATIONURL, AVAILABILITYURL, DATASELECTURL,
                 TEMPDIR, LOGDIR, LOGVERBOSITY, VERBOSITY, WEB, HTTPPORT,
                 EMAIL, SMTPADDRESS, SMTPPORT)
DYNAMIC_ARGS = (VERSION, HELP_CMD, FULLHELP)

# default values (for non-boolean parameters)
DEFAULT_ASDF_FILENAME = 'asdf.h5'
DEFAULT_AVAILABILITYURL = 'http://service.iris.edu/fdsnws/availability/1/query'
DEFAULT_DATADIR = 'data'
DEFAULT_DATASELECTURL = 'http://service.iris.edu/fdsnws/dataselect/1/query'
DEFAULT_DOWNLOADRETRIES = 3
DEFAULT_DOWNLOADWORKERS = 5
DEFAULT_EMAILFROM = 'noreply@rover'
DEFAULT_FILE = join('rover.config')
DEFAULT_FORCEFAILURES = 0
DEFAULT_HTTPBINDADDRESS = '127.0.0.1'
DEFAULT_HTTPPORT = 8000
DEFAULT_HTTPRETRIES = 3
DEFAULT_HTTPTIMEOUT = 60
DEFAULT_LOGDIR = 'logs'
DEFAULT_LOGVERBOSITY = 4
DEFAULT_LOGSIZE = '10M'
DEFAULT_LOGCOUNT = 10
DEFAULT_LOGUNIQUE_EXPIRE = 7
DEFAULT_MSEEDINDEXCMD = 'mseedindex -sqlitebusyto 60000'
DEFAULT_MSEEDINDEXWORKERS = 10
DEFAULT_OUTPUT_FORMAT = 'mseed'
DEFAULT_RECHECKPERIOD = 12
DEFAULT_ROVERCMD = 'rover'
DEFAULT_SMTPADDRESS = 'localhost'
DEFAULT_STATIONURL = 'http://service.iris.edu/fdsnws/station/1/query'
DEFAULT_SUBSCRIPTIONSDIR = 'subscriptions'
DEFAULT_TEMPDIR = 'tmp'
DEFAULT_TEMPEXPIRE = 1
DEFAULT_TIMESPANINC = 0.5
DEFAULT_TIMESPANTOL = 0.5
DEFAULT_VERBOSITY = 4


DIRVAR = 'DIR'
FILEVAR = 'FILE'
SAMPLESVAR = 'SAMPLES'
NVAR = 'N'
CMDVAR = 'CMD'
DAYSVAR = 'DAYS'
SECSVAR = 'SECS'
HOURSVAR = 'HOURS'
PERCENTVAR = 'PERCENT'
ADDRESSVAR = 'ADDRESS'
URLVAR = 'URL'
SIZE = 'SIZE'

def parse_bool(value):
    """
    Treat caseless true, yes and on and true, anything else as false.
    """
    if not value:
        value = 'False'
    value = value.lower()
    return value in ('true', 'yes', 'on')


class StoreBoolAction(Action):
    """
    We need a special action for booleans because we must covertly
    parse them as '--foo True' even though the user only types '--foo'.
    """

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


class FullHelpAction(Action):
    """
    Associate -H or --full-help with all help details.
    """

    def __init__(self,
                 option_strings,
                 dest=SUPPRESS,
                 default=SUPPRESS,
                 help=None):
        super(FullHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_big_help()
        parser.exit()



def m(string): return '-' + string


def mm(string): return '--' + string


def unbar(string): return sub('_', '-', string)


def cmd_or_alias(cmd):
    """
    We use the 'type' of the command argument to handle aliases.  In this
    way we avoid having to have multiple checks elsewhere in the startup
    logic.
    """
    if cmd in (INIT, INIT_REPO):
        cmd = INIT_REPOSITORY
    return cmd


class Arguments(ArgumentParser):
    """
    Extend the standard arg parsing to:
    * scan initial args to find if config file location specifed
    * if config file is missing, generate defaults
    * read config file before command line args

    To do this correctly for boolean flags (which behave differently on
    the command line and in the config file) we also have to pre-process those.

    The aim is to:
    * have (almost) all config duplcaited, both in config and command line
    * have default config be self-documenting and discoverable
    """

    def __init__(self):
        super().__init__(fromfile_prefix_chars='@', prog='ROVER',
                         formatter_class=RawDescriptionHelpFormatter,
                         description='ROVER: Retrieval of Various Experiment data Robustly',
                         add_help=False,
                         epilog=dedent('''
                         Flags can be negated (eg --no-web).
                         Defaults are read from the configuration file (%s).
                         Type "rover help" for more information on available commands.''' % DEFAULT_FILE))
        self.register('action', 'store_bool', StoreBoolAction)
        # operation details
        operation_group = self.add_argument_group('general operation arguments')
        operation_group.add_argument(m(_h), mm(_help), action='store_true', help='show this help message and exit')
        operation_group.add_argument(m(H), mm(FULLHELP), action=FullHelpAction, help='show full help details')
        operation_group.add_argument(m(BIG_V), mm(VERSION), action='version', version='ROVER %s' % __version__)
        operation_group.add_argument(mm(FULLCONFIG), default=False, action='store_bool', help='initialize with full configuration file', metavar='')
        operation_group.add_argument(m(F), mm(FILE), default=DEFAULT_FILE, help='specify configuration file')
        # metavar must be empty string to hide value since user options
        # are flags that are automatically given values below.
        operation_group.add_argument(mm(DEV), default=False, action='store_bool', help='development mode (show exceptions)?', metavar='')
        operation_group.add_argument(mm(DELETEFILES), default=True, action='store_bool', help='delete temporary files?', metavar='')
        operation_group.add_argument(mm(MDFORMAT), default=False, action='store_bool', help='display help in markdown format?', metavar='')
        operation_group.add_argument(mm(FORCECMD), default=False, action='store_bool', help='force cmd use (dangerous)', metavar='')

        # the repository
        repository_group = self.add_argument_group('repository arguments')
        repository_group.add_argument(mm(DATADIR), default=DEFAULT_DATADIR, action='store', help='the data directory - data, timeseries.sqlite', metavar=DIRVAR)

        # retrieval
        retrieve_group = self.add_argument_group('retrieve arguments')
        retrieve_group.add_argument(mm(TIMESPANINC), default=DEFAULT_TIMESPANINC, action='store', help='fractional increment for starting next timespan', metavar=SAMPLESVAR, type=float)
        retrieve_group.add_argument(mm(TIMESPANTOL), default=DEFAULT_TIMESPANTOL, action='store', help='fractional tolerance for overlapping timespans', metavar=SAMPLESVAR, type=float)
        retrieve_group.add_argument(mm(DOWNLOADRETRIES), default=DEFAULT_DOWNLOADRETRIES, action='store', help='maximum number of attempts to download data', metavar=NVAR, type=int)
        retrieve_group.add_argument(mm(DOWNLOADWORKERS), default=DEFAULT_DOWNLOADWORKERS, action='store', help='number of download instances to run', metavar=NVAR, type=int)
        retrieve_group.add_argument(mm(ROVERCMD), default=DEFAULT_ROVERCMD, action='store', help='command to run rover', metavar=CMDVAR)
        retrieve_group.add_argument(mm(PREINDEX), default=True, action='store_bool', help='index before retrieval?', metavar='')
        retrieve_group.add_argument(mm(INGEST), default=True, action='store_bool', help='call ingest after retrieval?', metavar='')
        retrieve_group.add_argument(mm(INDEX), default=True, action='store_bool', help='call index after ingest?', metavar='')
        retrieve_group.add_argument(mm(POSTSUMMARY), default=True, action='store_bool', help='call summary after retrieval?', metavar='')
        retrieve_group.add_argument(mm(OUTPUT_FORMAT), default=DEFAULT_OUTPUT_FORMAT, action='store', help='output data format. Choose from "mseed" (miniSEED) or "asdf" (ASDF)', metavar='')
        retrieve_group.add_argument(mm(ASDF_FILENAME), default=DEFAULT_ASDF_FILENAME, action='store', help='name of ASDF file when ASDF output is specified', metavar='')

        # metadata retrieval
        retrieve_md_group = self.add_argument_group('retrieve-metadata arguments')
        retrieve_md_group.add_argument(mm(STATIONURL), default=DEFAULT_STATIONURL, action='store', help='station service url', metavar=URLVAR)
        retrieve_md_group.add_argument(mm(FORCE_METADATA_RELOAD), default=False, action='store_bool', help='force reload of metadata', metavar='')

        # downloads
        download_group = self.add_argument_group('download arguments')
        download_group.add_argument(mm(AVAILABILITYURL), default=DEFAULT_AVAILABILITYURL, action='store', help='availability service url', metavar=URLVAR)
        download_group.add_argument(mm(DATASELECTURL), default=DEFAULT_DATASELECTURL, action='store', help='dataselect service url', metavar=URLVAR)
        download_group.add_argument(mm(TEMPDIR), default=DEFAULT_TEMPDIR, action='store', help='temporary storage for downloads', metavar=DIRVAR)
        download_group.add_argument(mm(TEMPEXPIRE), default=DEFAULT_TEMPEXPIRE, action='store', help='number of days before deleting temp files', metavar=DAYSVAR, type=int)
        download_group.add_argument(mm(HTTPTIMEOUT), default=DEFAULT_HTTPTIMEOUT, action='store', help='timeout for HTTP requests', metavar=SECSVAR, type=int)
        download_group.add_argument(mm(HTTPRETRIES), default=DEFAULT_HTTPRETRIES, action='store', help='max retries for HTTP requests', metavar=NVAR, type=int)
        download_group.add_argument(mm(FORCEFAILURES), default=DEFAULT_FORCEFAILURES, action='store', help='force failures for testing (dangerous)', metavar=PERCENTVAR, type=int)
        download_group.add_argument(mm(SORTINPYTHON), default=False, action='store_bool', help='avoid OS sort (slower)?', metavar='')

        # index
        index_group = self.add_argument_group('index arguments')
        index_group.add_argument(mm(ALL), default=False, action='store_bool', help='process all files (not just modified)?', metavar='')
        index_group.add_argument(mm(RECURSE), default=True, action='store_bool', help='when given a directory, process children?', metavar='')

        # subscription
        subscription_group = self.add_argument_group('subscription arguments')
        subscription_group.add_argument(mm(SUBSCRIPTIONSDIR), default=DEFAULT_SUBSCRIPTIONSDIR, action='store', help='directory for subscriptions', metavar=DIRVAR)
        subscription_group.add_argument(mm(RECHECKPERIOD), default=DEFAULT_RECHECKPERIOD, action='store', help='time between availabilty checks', metavar=HOURSVAR, type=int)
        subscription_group.add_argument(mm(FORCEREQUEST), default=False, action='store_bool', help='skip overlap checks (dangerous)?', metavar='')

        # logging
        logging_group = self.add_argument_group('logging arguments')
        logging_group.add_argument(mm(LOGDIR), default=DEFAULT_LOGDIR, action='store', help='directory for logs', metavar=DIRVAR)
        logging_group.add_argument(mm(LOGUNIQUE), default=False, action='store_bool', help='unique log names (with PIDs)?', metavar='')
        logging_group.add_argument(mm(LOGUNIQUEEXPIRE), default=DEFAULT_LOGUNIQUE_EXPIRE, action='store', help='number of days before deleting unique logs', metavar=DAYSVAR, type=int)
        logging_group.add_argument(mm(LOGVERBOSITY), default=DEFAULT_LOGVERBOSITY, action='store', help='log verbosity (0-6)', metavar=NVAR, type=int)
        logging_group.add_argument(mm(LOGSIZE), default=DEFAULT_LOGSIZE, action='store', help='maximum log size (e.g. 10M)', metavar=SIZE)
        logging_group.add_argument(mm(LOGCOUNT), default=DEFAULT_LOGCOUNT, action='store', help='maximum number of logs', metavar=NVAR, type=int)
        logging_group.add_argument(m(LITTLE_V), mm(VERBOSITY), default=DEFAULT_VERBOSITY, action='store', help='console verbosity (0-6)', metavar=NVAR, type=int)

        # mseedindex
        mseedindex_group = self.add_argument_group('mseedindex arguments')
        mseedindex_group.add_argument(mm(MSEEDINDEXCMD), default=DEFAULT_MSEEDINDEXCMD, action='store', help='mseedindex command', metavar=CMDVAR)
        mseedindex_group.add_argument(mm(MSEEDINDEXWORKERS), default=DEFAULT_MSEEDINDEXWORKERS, action='store', help='number of mseedindex instances to run', metavar=NVAR, type=int)

        # user feedback
        user_feedback_group = self.add_argument_group('user feedback arguments')
        user_feedback_group.add_argument(mm(WEB), default=True, action='store_bool', help='auto-start the download progress web server?', metavar='')
        user_feedback_group.add_argument(mm(HTTPBINDADDRESS), default=DEFAULT_HTTPBINDADDRESS, action='store', help='bind address for HTTP server', metavar=ADDRESSVAR)
        user_feedback_group.add_argument(mm(HTTPPORT), default=DEFAULT_HTTPPORT, action='store', help='port for HTTP server', metavar=NVAR, type=int)
        user_feedback_group.add_argument(mm(EMAIL), default='', action='store', help='address for completion status', metavar=ADDRESSVAR)
        user_feedback_group.add_argument(mm(EMAILFROM), default=DEFAULT_EMAILFROM, action='store', help='from address for email', metavar=ADDRESSVAR)
        user_feedback_group.add_argument(mm(SMTPADDRESS), default=DEFAULT_SMTPADDRESS, action='store', help='address of SMTP server', metavar=ADDRESSVAR)
        user_feedback_group.add_argument(mm(SMTPPORT), default=SMTP_PORT, action='store', help='port for SMTP server', metavar=NVAR, type=int)

        # commands / args
        self.add_argument(COMMAND, metavar='COMMAND', nargs='?', type=cmd_or_alias, help='use "help" for further information')
        self.add_argument(ARGS, nargs='*', help='command arguments (depend on the command)')

    def parse_args(self, args=None, namespace=None):
        """
        Intercept normal arg parsing to:
        * scan initial args to find if config file location specified
        * if config file is missing, generate defaults
        * read config file before command line args
        If there's an error here - in particular, if the config file does not exist -
        then we continue with Nones, so that we can generate the log before raising
        an error in Config.
        """
        if args is None:
            args = sys.argv[1:]
        args = self.__preprocess_booleans(args)
        config = None
        # we run this to parse and isolate the command, but will re-run below
        # once the config file is known
        command = super().parse_args(args=args).command
        if command != INIT_REPOSITORY:
            config, args = self.__extract_config(args)
            if exists(config):
                args = self.__patch_config(args, config)

        ns = super().parse_args(args=args, namespace=namespace)

        # support rover <command> -h and rover <command> --help usage
        if mm(_help) in args or m(_h) in args:
            if command:
                ns.command = HELP_CMD
                ns.args.append(command)

        return ns, config

    def __preprocess_booleans(self, args):
        """
        Replace --foo with '--foo True' and --no-foo with '--foo False'.
        This makes the interface consistent with the config file (which has
        the format 'foo=True') while letting the user type simple flags.
        """
        indices = []
        for (index, arg) in enumerate(args):
            if arg.startswith(NO):
                arg = mm(arg[5:])
            for action in self._actions:
                name = mm(unbar(action.dest))
                if name == arg and type(action) is StoreBoolAction:
                    indices.append(index)
        for index in reversed(indices):
            negative = args[index].startswith(NO)
            if negative:
                args[index] = mm(args[index][5:])
            args.insert(index+1, str(not negative))
        return args

    def __extract_config(self, args):
        """
        Find the config file, if given, otherwise use the default.
        This must be done before argument parsing because we need
        to add the contents of the file to the arguments (that is
        how the file is read).
        """
        config, indices = None, []
        # find all occurences of file params, saving last
        for (index, arg) in enumerate(args):
            # must skip file name
            if arg in ('-f', '--file') and (not indices or index+1 != indices[-1]):
                if index+1 >= len(args):
                    raise Exception('No argument for %s' % arg)
                indices.append(index)
                config = args[index+1]
        # remove all occurrences
        for index in reversed(indices):
            args = args[:index] + args[index+2:]
        if not config:
            config = self.get_default(FILE)
        config = canonify(config)
        # include config flag so that it is set correctly, even if the extracted
        # value is the one that is used here
        return config, [mm(FILE), config] + args

    def write_config(self, path, args, **kargs):
        """
        If the config file is missing, fill it with values.
        If args is None, defaults are used.
        If keywords are specified, they over-ride defaults and args.
        """
        create_parents(path)

        if "WRITE_FULL_CONFIG" in kargs and not kargs["WRITE_FULL_CONFIG"]:
            actions = [action for action in self._actions if unbar(action.dest) in LITTLE_CONFIG]
        else:
            actions = self._actions

        with open(path, 'w') as out:
            for action in actions:
                name, default = action.dest, action.default
                if unbar(name) not in DYNAMIC_ARGS:
                    if default is not None:
                        if name in kargs:
                            value = kargs[name]
                        elif args is not None:  # py2.7 no __bool__ on values
                            value = getattr(args, name)
                        else:
                            value = default
                        if action.help:
                            out.write('# %s\n' % action.help)
                        out.write('%s=%s\n' % (unbar(name), value))

    def __patch_config(self, args, config):
        """
        Force the reading of the config file (ignored for init-repository).
        """
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

    @staticmethod
    def __document_action(action):
        name = unbar(action.dest)
        unit = action.metavar
        default = action.default
        help = action.help
        if unit in (SECSVAR, HOURSVAR, DAYSVAR, PERCENTVAR, SAMPLESVAR):
            help = '%s (%s)' % (help, unit.lower())
        if name == FILE:
            name += ' / -f'
        elif name == HELP_CMD:
            name += ' / -h'
            default = False
            help = help.replace('this', 'the')
        elif name == FULLHELP:
            name += ' / -H'
            default = False
            help = help.replace('this', 'the')
        if help:
            help = help[0].upper() + help[1:]
        return name, default, help

    def __documentation(self, name):
        for action in self._actions:
            if name == unbar(action.dest):
                return self.__document_action(action)
        raise Exception('Unknown parameter %s' % name)

    def __documentation_names(self):
        for action in self._actions:
            name = unbar(action.dest)
            if name not in (COMMAND, ARGS):
                yield name

    NAME_WIDTH = 19
    DEFAULT_WIDTH = 20
    DESCRIPTION_WIDTH = 30

    def __print_docs_table_row(self, name, default, description):
        print('| %-*s | %-*s | %-*s |' %(self.NAME_WIDTH, name, self.DEFAULT_WIDTH, default, self.DESCRIPTION_WIDTH, description))

    def print_docs_header(self):
        """
        Print the table header row.
        """
        self.__print_docs_table_row(' Name', 'Default', 'Description')
        self.__print_docs_table_row('-' * self.NAME_WIDTH, '-' * self.DEFAULT_WIDTH, '-' * self.DESCRIPTION_WIDTH)

    def print_docs_row_md(self, name):
        """
        Print a table entry for the give argument, markdown formatted
        """
        self.__print_docs_table_row(*self.__documentation(name))

    def print_docs_row_text(self, name):
        """
        Print a table entry for the give argument, text formatted
        """
        name, default, description = self.__documentation(name)
        left = '| %-*s | %-*s' % (self.NAME_WIDTH, name, self.DEFAULT_WIDTH, default)
        right = ' | %-*s |' % (self.DESCRIPTION_WIDTH, description)
        if len(left + right) > 79:
            print('%s\n%77s |' % (left, description))
        else:
            print(left + right)

    def __print_docs_rows_md(self):
        for name in self.__documentation_names():
            self.print_docs_row_md(name)

    def print_docs_table_md(self):
        """
        Print all arguments in a table (called externally from python to generate docs).
        """
        self.print_docs_header()
        self.__print_docs_rows_md()

    def print_big_help(self, file=None):
        """
        With the new -H / --full-help option to the old implementation,
        """
        if file is None:
            file = sys.stdout
        self._print_message(self.format_big_help(), file)

    def print_help(self, file=None):
        """
        Subvert the -h and --help options to only print a restricted set of options.
        """
        if file is None:
            file = sys.stdout
        self._print_message(self.format_little_help(), file)

    def format_big_help(self):
        """
        A hacked version of format_help that prints big welcome message and
        includes all commands / actions.
        """
        formatter = self._get_formatter()
        formatter.add_text(self.description)
        formatter.add_text(self.welcome_big_help())
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            for action in action_group._group_actions:
                formatter.add_argument(action)
            formatter.end_section()
        formatter.add_text(self.epilog)
        return formatter.format_help()

    def format_little_help(self):
        """
        A hacked version of format_help that prints short welcome message and
        is restricted to common commands and actions in LITTLE_HELP.
        """
        formatter = self._get_formatter()
        formatter.add_text(self.description)
        formatter.add_text(self.welcome())
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            for action in action_group._group_actions:
                if unbar(action.dest) in LITTLE_HELP:
                    formatter.add_argument(action)
            formatter.end_section()
        formatter.add_text(self.epilog)
        return formatter.format_help()

    def welcome(self):
        from rover import COMMON_COMMANDS   # avoid import loop
        return ('Usage:\n'
                '  rover <command> [args]\n\n'
                'common commands:\n'
                '{0}\n\n'
                .format(dictionary_text_list(COMMON_COMMANDS)))

    def welcome_big_help(self):
        from rover import COMMON_COMMANDS, ADVANCED_COMMANDS   # avoid import loop
        return ('Usage:\n'
                '  rover <command> [args]\n\n'
                'common commands:\n'
                '{}\n\n'
                'advanced commands:\n'
                '{}\n\n'
                .format(dictionary_text_list(COMMON_COMMANDS),
                        dictionary_text_list(ADVANCED_COMMANDS)))


def fail_early(config):
    """
    Check commands so that we fail early.
    """
    check_cmd(config, ROVERCMD, 'rover')
    check_cmd(config, MSEEDINDEXCMD, 'mseedindex')
    workers = config.arg(DOWNLOADWORKERS)
    if workers > 10:
        raise Exception('Too many workers - risks overloading data center services (%s %d)' %
                        (mm(DOWNLOADWORKERS), workers))
    elif workers > 5:
        config.log.warn('Many workers - data center may refuse service (%s %d)' %
                        (mm(DOWNLOADWORKERS), workers))
    if config.arg(OUTPUT_FORMAT).upper() == "ASDF":
        try:
            import pyasdf
            import obspy
        except ImportError:
            raise Exception("Missing required 'pyasdf' python "
                            "package for 'output-format=asdf'")


class UserFeedback:
    """
    Display info on web and email status.
    """
    # can't put this in utils because we get a dependency loop.

    def __init__(self, config):
        self._log = config.log
        self._web = config.arg(WEB)
        self._url = 'http://%s:%s' % (config.arg(HTTPBINDADDRESS), config.arg(HTTPPORT))
        self._email = config.arg(EMAIL)

    def display_feedback(self):
        if self._web:
            self._log.default('Status available at %s' % self._url)
        else:
            self._log.info('No web status (see %s configuration parameter)' % mm(WEB))
        if self._email:
            self._log.default('Email status will be sent to %s' % self._email)
        else:
            self._log.info('No email status (see %s configuration parameter)' % mm(EMAIL))
