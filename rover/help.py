
from re import sub

from .args import HELP, LIST_INDEX, DATADIR, INIT_REPOSITORY, RETRIEVE, TEMPDIR, INGEST, INDEX, SUBSCRIBE, \
    AVAILABILITYURL, DATASELECTURL, DOWNLOAD, LIST_RETRIEVE, mm, ALL, MSEEDINDEXCMD, Arguments, MDFORMAT, FILE, START, \
    STATUS, STOP, LIST_SUBSCRIBE, UNSUBSCRIBE, TRIGGER, DAEMON, LIST_SUMMARY, SUMMARY, DEFAULT_FILE, INIT_REPO, INIT, \
    RETRIEVE_METADATA

"""
The 'rover help' command.
"""


BACKGROUND = 'background'
USAGE = 'usage'
LOWLEVEL = 'low-level'


def welcome(config):
    return '''
                      Welcome to ROVER!

For more information on ROVER commands:

rover %s %s

  Displays information on the most common commands to immediately
  download and ingest data.

rover %s %s

  Covers ROVER's advanced mode, which allows ROVER to run as a
  continuous background process. Subscriptions, a form of request,
  are checked on a user defined time interval and data is downloaded
  when needed.

rover %s %s

  Lists lower-level commands that are less likely to be used.

Individual commands have their own help documentation.  See "rover %s %s".

For information on configuration parameters use:

  rover -h

    Displays a list of parameters that can be
provided via the command line flags or by the rover.config
file:

  %s

    Contains ROVER's default configuration values, which can be customized
    to change ROVER's actions.

To display this screen again, type "rover" or "rover help".

''' % (HELP, USAGE,
       HELP, BACKGROUND,
       HELP, LOWLEVEL,
       HELP, HELP,
       DEFAULT_FILE)


def usage(config):
    return '''
                    Common ROVER Commands

rover %s [directory]

  Initializes a given directory, or the current directory
  if no argument is provided, as a ROVER data repository.
  %s will create a configuration file, by default %s,
  as well as directories for logs and data.

  The aliases `rover %s` and `rover %s` also exist.

rover %s (file | sta=... [start [end]] | N_S_L_C [start [end]])

  Compares ROVER's local index with remotely available data,
  then downloads and ingest files missing from the local
  repository. The location of remote data availability is
  determined by the config parameter %s, and the data is
  downloaded from the URL that is configured by the parameter %s.
  Use %s to determine data available on the remote server which
  is not in the local repository.

rover %s (file | sta=... [start [end]] | N_S_L_C [start [end]])

  Compares the local index with the data available remotely,
  then displays the difference. Note that the summary is
  printed to stdout, while logging is to stderr.

rover %s ...

  List index entries for the repository, config parameter %s,
  that match the given constraints. For more information,
  run "rover %s" with no arguments.

rover %s ...

  List summary entries for the repository, config parameter
  %s, that match the given constraints.  This is faster than
  `rover %s` but gives less detail.  For more information,
  run "rover %s" with no arguments.

''' % (INIT_REPOSITORY, INIT_REPOSITORY, DEFAULT_FILE, INIT, INIT_REPO,
       RETRIEVE, AVAILABILITYURL, DATASELECTURL, LIST_RETRIEVE,
       LIST_INDEX, DATADIR, LIST_INDEX,
       LIST_SUMMARY, DATADIR, LIST_INDEX, LIST_SUMMARY)


def background(config):
    return '''
                   Advanced ROVER Commands

rover %s

  Start the background process that regularly downloads subscriptions.

rover %s

rover %s

  Display the status of, and stop, the background process.

rover %s (file | sta=... [start [end]] | N_S_L_C [start [end]])

  Subscribe generates a background service (daemon) that regularly compares data
  available at the configured server with the local repository. If there is a
  discrepancy, available data is downloaded, ingested and indexed. `rover %s` is
  similar to `rover %s` but uses a daemon to regularly update the local repository.

rover %s

rover %s N

  Displays indices of all ROVER subscriptions. `rover %s` is similar to
  `rover %s`.

rover %s N

  Ask the daemon to immediately re-process a subscription(s) based
  on the subscription's index.

rover %s N

  Delete one or more subscriptions identified by their indices.
  Data associated with the subscription(s) is not deleted.

''' % (START, STATUS, STOP,
       SUBSCRIBE, SUBSCRIBE, RETRIEVE,
       LIST_SUBSCRIBE, LIST_SUBSCRIBE, LIST_SUBSCRIBE, LIST_RETRIEVE,
       TRIGGER, UNSUBSCRIBE)


def low_level(config):
    return '''
                   Low-Level ROVER Commands

The following commands are used internally, and are often less
useful from the command line:

rover %s url

  Downloads a single request, typically for a day, from a URL
  or a given file. File arguments are expected to contain fdsn
  web services requests and fetch data from the URL set by the
  parameter %s. Data are downloaded to a temporary directory
  configured by the parameter %s. After downloaded, data are
  ingested into the %s repository and are deleted from the temp
  directory. `rover %s` is called by %s, %s, and %s.

rover %s (file|dir) ...

  Adds contents from a miniSEED formatted file to ROVER's local
  repository and indexes the new data.

rover %s [(file|dir) ...]

  Indexes files, adds or changes entries in the tsindex table
  stored in the miniSEED database.

  When no argument is given, all modified files in the
  repository are processed. The `--all` flag forces
  all files to be processed. If a directory argument
  is provided, all files contained in the directory are
  processed, along with the contents of sub-directories,
  unless `--no-recurse` is specified.

rover %s

  Creates a summary of the index stored in a ROVER repository.
  This lists the overall span of data for each
  Net_Sta_Loc_Chan and can be queried using `rover %s`.

rover %s

  Download missing metadata from the fdsnws-station web service and save to the
  data archive. This feature is only supported for the ASDF output format.

''' % (DOWNLOAD, DATASELECTURL, TEMPDIR, DATADIR, DOWNLOAD, RETRIEVE,  SUBSCRIBE, DAEMON,
       INGEST,
       INDEX,
       SUMMARY, LIST_SUMMARY, RETRIEVE_METADATA)


GENERAL = {
    USAGE: (usage, 'General interactive use'),
    BACKGROUND: (background, 'Advanced use with ROVER in the background'),
    LOWLEVEL: (low_level, 'Rarely used, low-level commands')
}


class HelpFormatter:
    """
    Either print markdown verbatim. or strip markdown and re-justify for 80 columns.
    """

    def __init__(self, md_format):
        self._md_format = md_format

    def print(self, text):
        arguments = Arguments()
        first_param = True
        for line in self.__paras(text):
            if line.startswith('@'):
                if first_param:
                    arguments.print_docs_header()
                    first_param = False
                if self._md_format:
                    arguments.print_docs_row_md(line[1:])
                else:
                    arguments.print_docs_row_text(line[1:])
            elif self._md_format:
                print(self.__escape(line))
            elif line.startswith('#'):
                print(line.lstrip(' #'))
            else:
                for short in self.__splitlines(line):
                    print(short)

    def __escape(self, text):
        text = sub(r'\\', '\\\\', text)
        # text = sub(r'`', '\\`', text)
        return text

    def __paras(self, text):
        lines = text.splitlines()
        i = 1
        while i < len(lines):
            if lines[i].strip() and lines[i-1].strip() and not lines[i].startswith('@') and not lines[i-1].endswith('\\'):
                lines[i-1] = lines[i-1].rstrip() + ' ' + lines[i].strip()
                lines[i:] = lines[i+1:]
            else:
                i += 1
        return lines

    def __slurp(self, line):
        word = ''
        space = ''
        while line and not line[0] == ' ':
            word += line[0]
            line = line[1:]
        while line and line[0] == ' ':
            space += line[0]
            line = line[1:]
        return word, space, line

    def __splitlines(self, line):
        indentation = ''
        while line and line.startswith(' '):
            indentation += line[0]
            line = line[1:]
        if not line:
            yield ''
            return
        while line:
            short, space = indentation, ''
            line = line.lstrip()
            while line:
                word, next_space, next_line = self.__slurp(line)
                if short.strip() and len(short + space + word) > 78:
                    yield short
                    short, space = indentation, ''
                else:
                    short = short + space + word
                    space, line = next_space, next_line
            if short:
                yield short


class Helper(HelpFormatter):

    def __init__(self, config):
        super().__init__(config.arg(MDFORMAT))
        self._config = config

    def run(self, args):
        from rover import COMMANDS   # avoid import loop
        if not args:
            self.print(welcome(self._config))
            return
        elif len(args) == 1:
            command = args[0].lower()
            if command == 'help':
                self._help()
                return
            if command in COMMANDS:
                self.print(COMMANDS[command][0].__doc__)
                return
            elif command in GENERAL:
                self.print(GENERAL[command][0](self._config))
                return
        raise Exception('Help is available for: %s, %s, %s, and individual commands (or simply "rover help")' % (USAGE, BACKGROUND, LOWLEVEL))

    def _help(self):
        from rover import COMMANDS   # avoid import loop
        self.print('''
### Help

Gives help on the various commands.

Help is available for the following commands:
        ''')
        for command in sorted(COMMANDS.keys()):
            print('%19s: %s' % (command, COMMANDS[command][1]))
        print('''
Help is also available for the following general topics:
''')
        for command in GENERAL.keys():
            print('%19s: %s' % (command, GENERAL[command][1]))
        print('''
For example:

    rover help retrieve
''')
