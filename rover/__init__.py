
from .index import index
from .config import RoverArgumentParser, update_config, UPDATE_CONFIG, INDEX
from .logs import init_log


def welcome(args, log):
    print('''
                      Welcome to Rover!

  The following commands are available:
  
    %s
      Scan the mssed files in the local store (config
      parameter mseed-dir) and update the database index
      (config parameter database-file).

    %s
      Delete and re-write the configuration file.



  For more information on the parameters that modify Rover's behaviour 
  run "rover -h" or edit %s
  To redisplay this information run "rover" (with no command).
  
''' % (INDEX, UPDATE_CONFIG, args.file))

def execute(command, args, log):
    if not command:
        welcome(args, log)
    elif command == UPDATE_CONFIG:
        update_config(args, log)
    elif command == INDEX:
        index(args, log)
    else:
        print('TODO: %s' % command)

def main():
    argparse = RoverArgumentParser()
    args = argparse.parse_args()
    log = init_log(args, 'rover')
    log.info('args: %s' % args)
    execute(args.command, args, log)
