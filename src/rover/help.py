
from re import sub

from .args import HELP_CMD, LIST_INDEX, DATADIR, INIT_REPOSITORY, RETRIEVE, TEMPDIR, INGEST, INDEX, SUBSCRIBE, \
    AVAILABILITYURL, DATASELECTURL, DOWNLOAD, LIST_RETRIEVE, mm, ALL, MSEEDINDEXCMD, Arguments, MDFORMAT, FILE, START, \
    STATUS, STOP, LIST_SUBSCRIBE, UNSUBSCRIBE, TRIGGER, DAEMON, LIST_SUMMARY, SUMMARY, DEFAULT_FILE, INIT_REPO, INIT, \
    RETRIEVE_METADATA, WEB
from .utils import dictionary_text_list

"""
The 'rover help' command.
"""


BACKGROUND = 'background'
USAGE = 'usage'
LOWLEVEL = 'low-level'


def usage(config):
    return '''
                    Common ROVER Commands

rover {0} [directory]

  Initializes a given directory, or the current directory
  if no argument is provided, as a ROVER data repository.
  {0} will create a configuration file, by default {0},
  as well as directories for logs and data.

  The aliases `rover {1}` and `rover {2}` also exist.

rover {3} (file | sta=... [start [end]] | N_S_L_C [start [end]])

  Compares ROVER's local index with remotely available data,
  then downloads and ingest files missing from the local
  repository. The location of remote data availability is
  determined by the config parameter {4}, and the data is
  downloaded from the URL that is configured by the parameter {5}.
  Use {7} to determine data available on the remote server which
  is not in the local repository.

rover {6} (file | sta=... [start [end]] | N_S_L_C [start [end]])

  Compares the local index with the data available remotely,
  then displays the difference. Note that the summary is
  printed to stdout, while logging is to stderr.

rover {7} ...

  List index entries for the repository, config parameter %s,
  that match the given constraints. For more information,
  run "rover {7}" with no arguments.

rover {8} ...

  List summary entries for the repository, config parameter
  {9}, that match the given constraints.  This is faster than
  `rover {10}` but gives less detail.  For more information,
  run "rover {8}" with no arguments.

rover {11} <command>

  Gives help on the various commands.

'''.format(INIT_REPOSITORY, DEFAULT_FILE, INIT,
           RETRIEVE, AVAILABILITYURL, DATASELECTURL, LIST_RETRIEVE,
           LIST_INDEX, LIST_SUMMARY, DATADIR, LIST_INDEX,
           HELP_CMD)


def background(config):
    return '''
                   Advanced ROVER Commands

rover {0}

  Start the background process that regularly downloads subscriptions.

rover {1}

rover {2}

  Display the status of, and stop, the background process.

rover {3} (file | sta=... [start [end]] | N_S_L_C [start [end]])

  Subscribe generates a background service (daemon) that regularly compares data
  available at the configured server with the local repository. If there is a
  discrepancy, available data is downloaded, ingested and indexed. `rover {3}` is
  similar to `rover {4}` but uses a daemon to regularly update the local repository.

rover {5}

rover {5} N

  Displays indices of all ROVER subscriptions. `rover {5}` is similar to
  `rover {6}`.

rover {7} N

  Ask the daemon to immediately re-process a subscription(s) based
  on the subscription's index.

rover {8} N

  Delete one or more subscriptions identified by their indices.
  Data associated with the subscription(s) is not deleted.

'''.format(START, STATUS, STOP,
           SUBSCRIBE, RETRIEVE,
           LIST_SUBSCRIBE, LIST_RETRIEVE,
           TRIGGER, UNSUBSCRIBE)


def low_level(config):
    return '''
                   Low-Level ROVER Commands

The following commands are used internally, and are often less
useful from the command line:

rover {0} url

  Downloads a single request, typically for a day, from a URL
  or a given file. File arguments are expected to contain fdsn
  web services requests and fetch data from the URL set by the
  parameter {1}. Data are downloaded to a temporary directory
  configured by the parameter {2}. After downloaded, data are
  ingested into the {3} repository and are deleted from the temp
  directory. `rover {0}` is called by {4}, {5}, and {6}.

rover {7} [(file|dir) ...]

  Indexes files, adds or changes entries in the tsindex table
  stored in the miniSEED database.

  When no argument is given, all modified files in the
  repository are processed. The `--all` flag forces
  all files to be processed. If a directory argument
  is provided, all files contained in the directory are
  processed, along with the contents of sub-directories,
  unless `--no-recurse` is specified.

rover {8} (file|dir) ...

  Adds contents from a miniSEED formatted file to ROVER's local
  repository and indexes the new data.

rover {9} ... 

Starts a web server that provides information on the progress of the download
manager. ROVER's default configuration starts `rover {9}` automatically.
The flag`--no-web` prevents ROVER's web server from launching in accordance
with `rover {4}` or `rover {10}`.

rover {11} ...

  Download missing metadata from the fdsnws-station web service and save to
  the data archive. This feature is only supported for the ASDF output format.

rover {12} ...

  Creates a summary of the index stored in a ROVER repository.
  This lists the overall span of data for each
  Net_Sta_Loc_Chan and can be queried using `rover {13}`.

'''.format(DOWNLOAD, DATASELECTURL, TEMPDIR, DATADIR, RETRIEVE, SUBSCRIBE,
           DAEMON, INDEX, INGEST, WEB, START, RETRIEVE_METADATA, SUMMARY,
           LIST_SUMMARY)


GENERAL = {
    USAGE: (usage, 'General interactive use'),
    #BACKGROUND: (background, 'Advanced use with ROVER in the background'),
    LOWLEVEL: (low_level, 'Rarely used, low-level commands')
}


class HelpFormatter:
    """
    Either print markdown verbatim. or strip markdown and re-justify for 80 columns.
    """

    def __init__(self, md_format):
        self._md_format = md_format

    def print_help(self, text):
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
        return text.splitlines()

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
            self._help()
            return
        elif len(args) == 1:
            command = args[0].lower()
            if command == 'help':
                self._help()
                return
            if command in COMMANDS:
                self.print_help(COMMANDS[command][0].__doc__)
                return
            elif command in GENERAL:
                self.print_help(GENERAL[command][0](self._config))
                return
        raise Exception('Help is available for: %s, %s, %s, and individual commands (or simply "rover help")' % (USAGE, BACKGROUND, LOWLEVEL))

    def _help(self):
        from rover import COMMON_COMMANDS, ADVANCED_COMMANDS   # avoid import loop
        self.print_help('''
### Help

Gives help on the various commands.

Usage:

  rover help <command>

Help is available for the following:

Core commands:
{}

General topics:
{}

Advanced commands:
{}

For example:

    rover help retrieve

'''.format(dictionary_text_list(COMMON_COMMANDS),
           dictionary_text_list(GENERAL),
           dictionary_text_list(ADVANCED_COMMANDS)))
