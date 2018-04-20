
from logging import getLogger, StreamHandler, Formatter
from logging.handlers import RotatingFileHandler
from os.path import join, exists, isdir, expanduser
from os import makedirs
import sys


def level(n):
    '''
    Our log levels are 1-5 (quiet - verbose).
    Logging levels are 50-10 (quiet - verbose)
    '''
    return 10 * (6 - (max(min(n, 5), 1)))


def init_log(args, name, stdout=None):

    log = getLogger(name)

    dir = expanduser(args.log_dir)
    if not exists(dir):
        makedirs(dir)
    if not isdir(dir):
        raise Exception('"%s" is not a directory (log-dir)' % dir)

    time_formatter = Formatter('%(levelname)-8s %(asctime)s: %(message)s')
    path = join(dir, name + '.log')
    # smallest size is 8kB (2^13), largest szie 1MB (2^20)
    size = 2 ** (12 + max(min(args.log_size, 7), 1))
    count = max(min(args.log_count, 100), 1)
    file_handler = RotatingFileHandler(path, maxBytes=size, backupCount=count)
    file_handler.setLevel(level(args.log_verbosity))
    file_handler.setFormatter(time_formatter)
    log.addHandler(file_handler)

    name_formatter = Formatter('%(name)s %(levelname)8s: %(message)s')
    stdout_handler = StreamHandler(stdout if stdout else sys.stdout)
    stdout_handler.setLevel(level(args.verbosity))
    stdout_handler.setFormatter(name_formatter)
    log.addHandler(stdout_handler)

    return log
