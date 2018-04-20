
from logging import getLogger, StreamHandler
from logging.handlers import RotatingFileHandler
from os.path import join, exists, isdir, expanduser
from os import makedirs


def level(n):
    '''
    Our log levels are 1-5 (quiet - verbose).
    Logging levels are 50-10 (quiet - verbose)
    '''
    return 10 * (6 - (max(min(n, 5), 1)))


def init_log(args, name):

    log = getLogger(name)

    dir = expanduser(args.log_dir)
    if not exists(dir):
        makedirs(dir)
    if not isdir(dir):
        raise Exception('"%s" is not a directory (log-dir)' % dir)

    path = join(dir, name + '.log')
    size = 2 ** max(min(args.log_size, 10), 5)
    count = max(min(args.log_count, 100), 1)
    file_handler = RotatingFileHandler(path, maxBytes=size, backupCount=count)
    file_handler.setLevel(level(args.log_verbosity))
    log.addHandler(file_handler)
    log.error('Starting log to %s' % file_handler)

    stdout_handler = StreamHandler()
    stdout_handler.setLevel(level(args.verbosity))
    log.addHandler(stdout_handler)

    return log
