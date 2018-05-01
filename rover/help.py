
from .config import HELP, LIST_INDEX, MSEEDDIR, RESET_CONFIG, RETRIEVE, TEMPDIR, INGEST, INDEX, MSEEDDB, SUBSCRIBE, \
    AVAILABILITYURL, DATASELECTURL, DOWNLOAD

DAEMON = 'daemon'
USAGE = 'usage'
LOWLEVEL = 'low-level'


def help(args, log):
    if not args.args:
        welcome(args)
    elif len(args.args) == 1 and args.args[0] == USAGE:
        usage()
    elif len(args.args) == 1 and args.args[0] == DAEMON:
        daemon()
    elif len(args.args) == 1 and args.args[0] == LOWLEVEL:
        low_level()
    else:
        raise Exception('Help is available for: %s, %s, %s (or simply "rover help")' % (USAGE, DAEMON, LOWLEVEL))


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
       args.file))


def usage():
    print('''
                    Common ROVER Commands
                    
    rover %s (file|sncl start [end])
      Compare the local index (config parameter %s) with the data 
      availabe remotely (config parameter %s), then download 
      (config parameter %s) and ingest the missing files.

    rover %s ...
      List index entries for the local store (config parameter 
      %s) that match the given constraints.  For more information, 
      run "rover %s" (with no arguments).

    rover %s
      Delete and re-write the configuration file.
''' % (RETRIEVE, MSEEDDB, AVAILABILITYURL, DATASELECTURL,
       LIST_INDEX, MSEEDDIR, LIST_INDEX,
       RESET_CONFIG))


def daemon():
    print('''
                   Advanced ROVER Commands
''')


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
      parameter %s) and update the database index (config
      parameter %s).  Called by %s when needed.
      
    %s
      Scan the mseed files in the local store (config parameter 
      %s) and update the database index (config parameter 
      %s).  Called by %s when needed.
''' % (DOWNLOAD, TEMPDIR, MSEEDDIR, SUBSCRIBE,
       INGEST, MSEEDDIR, MSEEDDB, RETRIEVE,
       INDEX, MSEEDDIR, MSEEDDB, INGEST))
