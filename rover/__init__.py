
from .welcome import welcome
from .args import RoverArgumentParser
from .logs import init_log


def execute(command, args, log):
    if not command:
        welcome(args, log)
    else:
        print('TODO: %s' % command)

def main():
    argparse = RoverArgumentParser()
    args = argparse.parse_args()
    log = init_log(args, 'rover')
    execute(args.command, args, log)
