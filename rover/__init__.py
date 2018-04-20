from .index import index
from .args import RoverArgumentParser
from .logs import init_log


def welcome(args, log):
    print('''
                      Welcome to Rover!

  The following commands are available:
  
    index path [path...]
    
      This adds MSEED files at the given paths to the local repo
      and includes them in the database index.



  For more information on the parameters that modify Rover's behaviour 
  run "rover -h" or edit %s
  To redisplay this information run "rover" (with no command).

''' % args.file)

def execute(command, args, log):
    if not command:
        welcome(args, log)
    elif command == 'index':
        index(args, log)
    else:
        print('TODO: %s' % command)

def main():
    argparse = RoverArgumentParser()
    args = argparse.parse_args()
    log = init_log(args, 'rover')
    log.info('args: %s' % args)
    execute(args.command, args, log)
