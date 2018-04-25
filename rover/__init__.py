
from .ingest import ingest
from .index import index
from .config import RoverArgumentParser, reset_config, RESET_CONFIG, INDEX, MSEEDDB, MSEEDDIR, INGEST, LIST_STORE
from .logs import init_log


def welcome(args, log):
    print('''
                      Welcome to Rover!

  The following commands are available:
  
    %s (file|dir) ...
      Add the specified files to the local store (config
      parameter %s) and update the database index (config
      parameter %s).
      
    %s SNCL
      List contents of the local store (config parameter 
      %s) that match the given SNCL pattern.
  
    %s
      Scan the mseed files in the local store (config parameter 
      %s) and update the database index (config parameter 
      %s).  Unlikely to be useful directly - called 
      automatically when needed.

    %s
      Delete and re-write the configuration file.


  For more information on the parameters that modify Rover's behaviour 
  run "rover -h" or read %s
  To redisplay this information run "rover" (with no command).
  
''' % (INGEST, MSEEDDIR, MSEEDDB,
       LIST_STORE, MSEEDDIR,
       INDEX, MSEEDDIR, MSEEDDB,
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
    else:
        print('TODO: %s' % command)

def main():
    log = None
    try:
        argparse = RoverArgumentParser()
        args = argparse.parse_args()
        log = init_log(args, 'rover')
        log.info('args: %s' % args)
        execute(args.command, args, log)
    except Exception as e:
        if log:
            log.error(str(e))
            raise e  # remove after development
        else:
            raise e
