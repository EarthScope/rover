
from .args import HELP, LIST_INDEX, MSEEDDIR, RESET_CONFIG, RETRIEVE, TEMPDIR, INGEST, INDEX, MSEEDDB, SUBSCRIBE, \
    AVAILABILITYURL, DATASELECTURL, DOWNLOAD, COMPARE, COMPACT, mm, ALL, NO, MSEEDCMD, Arguments

"""
The 'rover help' command.
"""


DAEMON = 'daemon'
USAGE = 'usage'
LOWLEVEL = 'low-level'


def welcome(args):
    print('''
                      Welcome to ROVER!

  For more information on ROVER commands:
      
    rover %s %s
      Displays information on the most common commands to immediately 
      download and ingest data.
        
    rover %s %s
      Covers ROVER's advanced mode, where it runs in the background, 
      continuously checking subscriptions and downloading data when 
      needed.
        
    rover %s %s
      Lists lower-level commands that are less likely to be used.
      
  Individual commands also have help.  See "rover %s %s".
        
  For more information on configuration parameters, which can be 
  provided via a file or using command line flags:
  
    rover -h
      Displays the command line parameters.
      
    %s
      Contains the defaults for these parameters and can be edited 
      to change the default behaviour.
        
  To display this screen again, type "rover" or "rover help".
''' % (HELP, USAGE,
       HELP, DAEMON,
       HELP, LOWLEVEL,
       HELP, HELP,
       args.file))


def usage():
    print('''
                    Common ROVER Commands
                    
    rover %s (file|sncl start [end])
      Compare the local index (config parameter %s) with the data 
      availabe remotely (config parameter %s), then download 
      (config parameter %s) and ingest the missing files.  Use
      %s (below) to see what data would be downloaded (without
      doing the work).
      
    rover %s (file|sncl start [end])
      Compare the local index (config parameter %s) with the data 
      availabe remotely (config parameter %s), then display 
      the difference.  Note that the summary is printed to stdout, while
      logging is to stderr.

    rover %s ...
      List index entries for the local store (config parameter 
      %s) that match the given constraints.  For more information, 
      run "rover %s" (with no arguments).

    rover %s
      Delete and re-write the configuration file.
''' % (RETRIEVE, MSEEDDB, AVAILABILITYURL, DATASELECTURL, COMPARE,
       COMPARE, MSEEDDB, AVAILABILITYURL,
       LIST_INDEX, MSEEDDIR, LIST_INDEX,
       RESET_CONFIG))


def daemon():
    print('''
                   Advanced ROVER Commands
                   
    rover %s
      Subscribe to retrieve updates whenever they become available.
''' % (SUBSCRIBE,))


def low_level():
    print('''
                   Low-Level ROVER Commands
                   
  The following commands are used internally, but are usually not
  useful from the command line:
  
    %s url
      Download data from the given URL to the temporary store
      (config parameter %s).  When downloaded, ingest into the
      local store (config parameter %s) and delete.  Called
      by %s when needed.
  
    %s (file|dir) ...
      Add the specified files to the local store (config
      parameter %s), compact the contents, and update the 
      database index (config parameter %s).  Called by %s 
      when needed.
      
    %s [(file|dir)...]
      Rewrite mseed files, removing duplicates and joining contiguous 
      data, then (for files in the local store) update the database 
      index (config parameter %s).  Called by %s when needed.
      
      If no arguments are given then files in the local store
      (config parameter %s) that have been modified since the 
      store was last indexed are processed.  The config parameter 
      %s can be used (eg %s on the command line) to force 
      processing of all files in the store.
      
      The config parameter %s can be used (eg %s on the 
      command line) to avoid calling this command when ingesting data.
            
    %s [(file|dir) ...]
      Scan files and update the database index (config parameter 
      %s) using the mseedindex command (config parameter 
      %s). Called by %s or %s when needed.
      
      If no arguments are given then files in the local store
      (config parameter %s) that have been modified since the 
      store was last indexed are processed.  The config parameter 
      %s can be used (eg %s on the command line) to force 
      processing of all files in the store.
''' % (DOWNLOAD, TEMPDIR, MSEEDDIR, SUBSCRIBE,
       INGEST, MSEEDDIR, MSEEDDB, RETRIEVE,
       COMPACT, MSEEDDB, INGEST, MSEEDDIR, ALL, mm(ALL), COMPACT, NO+COMPACT,
       INDEX, MSEEDDB, MSEEDCMD, COMPACT, INGEST, MSEEDDIR, ALL, mm(ALL)))


GENERAL = {
    USAGE: (usage, 'General interactive use'),
    DAEMON: (daemon, 'Advanced use with rover in the backgrround'),
    LOWLEVEL: (low_level, 'Rarely used, low-level commands')
}


class Helper:

    def __init__(self, config):
        self._args = config.args
        self._md_format = self._args.md_format

    def run(self, args):
        from rover import COMMANDS   # avoid import loop
        if not args:
            welcome(self._args)
            return
        elif len(args) == 1:
            command = args[0].lower()
            if command == 'help':
                self._help()
                return
            if command in COMMANDS:
                self._print_formatted(COMMANDS[command][0].__doc__)
                return
            elif command in GENERAL:
                GENERAL[command][0](self._args)
                return
        raise Exception('Help is available for: %s, %s, %s (or simply "rover help")' % (USAGE, DAEMON, LOWLEVEL))

    def _print_formatted(self, text):
        arguments = Arguments()
        first_param = True
        for line in self._paras(text):
            if line.startswith('@'):
                if first_param:
                    arguments.print_docs_header()
                    first_param = False
                if self._md_format:
                    arguments.print_docs_row(line[1:])
                else:
                    arguments.print_docs_text(line[1:])
            elif self._md_format:
                print(line)
            elif line.startswith('#'):
                print(line.lstrip(' #'))
            else:
                for short in self._splitlines(line):
                    print(short)

    def _paras(self, text):
        lines = text.splitlines()
        i = 1
        while i < len(lines):
            if lines[i].strip() and lines[i-1].strip() and not lines[i].startswith('@'):
                lines[i-1] = lines[i-1].rstrip() + ' ' + lines[i]
                lines[i:] = lines[i+1:]
            else:
                i += 1
        return lines

    def _slurp(self, line):
        word = ''
        space = ''
        while line and not line[0] == ' ':
            word += line[0]
            line = line[1:]
        while line and line[0] == ' ':
            space += line[0]
            line = line[1:]
        return word, space, line

    def _splitlines(self, line):
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
                word, next_space, next_line = self._slurp(line)
                if len(short + space + word) > 78:
                    yield short
                    short, space = indentation, ''
                else:
                    short = short + space + word
                    space, line = next_space, next_line
            if short:
                yield short

    def _help(self):
        from rover import COMMANDS   # avoid import loop
        print('''
Help

Gives help on the various commands.
        
Help is available for the following commands:
        ''')
        for command in sorted(COMMANDS.keys()):
            print('%15s: %s' % (command, COMMANDS[command][1]))
        print('''
Help is also available for the following general topics: 
''')
        for command in GENERAL.keys():
            print('%15s: %s' % (command, GENERAL[command][1]))
        print('''
For example:

    rover help retrieve
''')
