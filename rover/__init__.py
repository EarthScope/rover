
from .args import RoverArgumentParser
from .logs import init_log


def main():
    argparse = RoverArgumentParser()
    args = argparse.parse_args()
    log = init_log(args, 'rover')
    log.debug('args: %s' % args)
    log.error('hello world')
