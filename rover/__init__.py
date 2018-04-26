
from .list import list_index
from .ingest import ingest
from .index import index
from .config import RoverArgumentParser, reset_config, RESET_CONFIG, INDEX, MSEEDDB, MSEEDDIR, INGEST, LIST_INDEX
from .logs import init_log


def welcome(args, log):
    print('''
                      Welcome to Rover!

  The following commands are available:
  
    %s (file|dir) ...
      Add the specified files to the local store (config
      parameter %s) and update the database index (config
      parameter %s).
      
    %s ...
      List index entries for the local store (config parameter 
      %s) that match the given constraints.  For more information, 
      run "rover %s" (with no arguments).
  
    %s
      Scan the mseed files in the local store (config parameter 
      %s) and update the database index (config parameter 
      %s).  Called by %s when needed.

    %s
      Delete and re-write the configuration file.


  For more information on the parameters that modify Rover's behaviour 
  run "rover -h" or read %s
  To redisplay this information run "rover" (with no command).
  
''' % (INGEST, MSEEDDIR, MSEEDDB,
       LIST_INDEX, MSEEDDIR, LIST_INDEX,
       INDEX, MSEEDDIR, MSEEDDB, INGEST,
       RESET_CONFIG,
       args.file))


def execute(command, args, log):
    if not command:
        welcome(args, log)
    elif command == RESET_CONFIG:
        reset_config(args, log)
    elif command == INDEX:
        index(args, log)
    elif command == INGEST:
        ingest(args, log)
    elif command == LIST_INDEX:
        list_index(args, log)
    else:
        raise Exception('Unknown command %s' % command)


def main():
    log = None
    try:
        argparse = RoverArgumentParser()
        args = argparse.parse_args()
        log = init_log(args.log_dir, args.log_size, args.log_count, args.log_verbosity, args.verbosity, 'rover')
        log.info('args: %s' % args)
        execute(args.command, args, log)
    except Exception as e:
        if log:
            log.error(str(e))
            if not args or args.dev:
                raise e
        else:
            raise e
