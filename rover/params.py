
from argparse import ArgumentParser, Action
from os.path import exists, expanduser
import sys


class StoreBoolAction(Action):

    def __init__(self,
                 option_strings,
                 dest,
                 default=None,
                 choices=None,
                 required=False,
                 help=None):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=1,
            const=None,
            default=default,
            type=bool,
            choices=choices,
            required=required,
            help=help,
            metavar=None)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


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
        super().__init__(description='ROVER: Retrieval of Various Experiment data Robustly')
        self.register('action', 'store_bool', StoreBoolAction)
        # TODO - windows needs different path
        self.add_argument('-f', '--file', default="~/.rover", help='specify configuration file')
        self.add_argument('--daemon', default=False, action='store_bool', help='use background daemons')

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
        return super().parse_args(args=args, namespace=namespace)

    def preprocess_booleans(self, args):
        # find any booleans
        indices = []
        for (index, arg) in enumerate(args):
            if arg.startswith('--no-'):
                arg = '--' + arg[5:]
            for action in self._actions:
                if '--' + action.dest == arg and type(action) is StoreBoolAction:
                    indices.append(index)
        # insert literal values for command line flags
        for index in reversed(indices):
            negative = args[index].startswith('--no-')
            args.insert(index+1, str(not negative))
        return args

    def extract_config(self, args):
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
            config = self.get_default('file')
        return config, args

    def generate_default_config(self, config):
        config = expanduser(config)
        if not exists(config):
            with open(config, 'w') as out:
                for action in self._actions:
                    if action.dest not in ('help', 'file'):
                        if action.default:
                            if action.help:
                                out.write('# %s\n' % action.help)
                            out.write('%s=%s\n' % (action.dest, action.default))
        return

    def patch_config(self, args, config):
        return args

