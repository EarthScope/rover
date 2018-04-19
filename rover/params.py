
from argparse import ArgumentParser, Action
from os.path import exists, expanduser
import sys


NO = '--no-'
DAEMON = 'daemon'
F, FILE = 'f', 'file'
HELP = 'help'
CONFIG = '~/.rover'


def parse_bool(value):
    '''
    Treat caseless true, yes and on and true, anthing else as false.
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
        setattr(namespace, self.dest, values)



def m(string): return '-' + string
def mm(string): return '--' + string


class RoverArgumentParser(ArgumentParser):

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
                         description='ROVER: Retrieval of Various Experiment data Robustly',
                         epilog='Defaults are read from the configuration file '
                                +'(default %s; written on first use). ' % CONFIG
                                +'Flags can be negated (eg --no-daemon).')
        self.register('action', 'store_bool', StoreBoolAction)
        # TODO - windows needs different path
        self.add_argument(m(F), mm(FILE), default=CONFIG, help='specify configuration file')
        # metavar must be empty string to hide value since user options
        # are flags that are automatically given values below.
        self.add_argument(mm(DAEMON), default=False, action='store_bool', help='use background processes', metavar='')

    def parse_args(self, args=None, namespace=None):
        '''
        Intercept normal arg parsing to:
        * scan initial args to find if config file location specifed
        * if config file is missing, generate defaults
        * read config file before command line args
        '''
        if args is None:
            args = sys.argv[1:]
        args = self.preprocess_booleans(args)
        config, args = self.extract_config(args)
        self.generate_default_config(config)
        args = self.patch_config(args, config)
        print(args)
        return super().parse_args(args=args, namespace=namespace)

    def preprocess_booleans(self, args):
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
                if '--' + action.dest == arg and type(action) is StoreBoolAction:
                    indices.append(index)
        for index in reversed(indices):
            negative = args[index].startswith(NO)
            if negative:
                args[index] = mm(args[index][5:])
            args.insert(index+1, str(not negative))
        return args

    def extract_config(self, args):
        '''
        Find the config file, if given, otherwise use the default.
        This must be done before arrgument parsing because we need
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
        config = expanduser(config)
        # include config flag so that it is set correctly, even if the extracted
        # value is th eone that is used here
        return config, [mm(FILE), config] + args

    def generate_default_config(self, config):
        '''
        If the config file is missing, fill it with default values.
        '''
        if not exists(config):
            with open(config, 'w') as out:
                for action in self._actions:
                    if action.dest not in (HELP, FILE):
                        if action.default is not None:
                            if action.help:
                                out.write('# %s\n' % action.help)
                            out.write('%s=%s\n' % (action.dest, action.default))
        return

    def patch_config(self, args, config):
        '''
        Force the reading of the config file.
        '''
        return ['@'+config] + args

    def convert_arg_line_to_args(self, arg_line):
        '''
        Parse the config file, constructing '--name value" from name=value
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
