
import sys
from logging import getLogger, StreamHandler, Formatter, DEBUG
from logging.handlers import RotatingFileHandler
from os import makedirs, getpid
from os.path import join, exists, isdir, expanduser
from re import match

from .utils import clean_old_files


def level(n):
    '''
    Our log levels are 0-5 (silent - verbose).
    Logging levels are 50-10 (quiet - verbose)
    '''
    return 10 * (6 - (max(min(n, 5), 0)))


def match_unique(name):
    return match(r'\w+_\d+\.log', name)


def init_log(log_dir, log_size, log_count, log_verbosity, verbosity, name, log_unique, log_unique_expire, stderr=None):
    """
    Create a log with two handlers.
    One handler is a rotated file, the other stderr.
    The file is for details, stderr for errors to the user.
    """

    if log_unique:
        name = '%s.%d' % (name, getpid())

    log = getLogger(name)
    log.setLevel(DEBUG)

    dir = expanduser(log_dir)
    if not exists(dir):
        makedirs(dir)
    if not isdir(dir):
        raise Exception('"%s" is not a directory (log-dir)' % dir)

    time_formatter = Formatter('%(levelname)-8s %(asctime)s: %(message)s')
    path = join(dir, name + '.log')
    # smallest size is 8kB (2^13), largest size 4MB (2^22)
    size = 2 ** (12 + max(min(log_size, 10), 1))
    count = max(min(log_count, 100), 1)
    file_handler = RotatingFileHandler(path, maxBytes=size, backupCount=count)
    file_handler.setLevel(level(log_verbosity))
    file_handler.setFormatter(time_formatter)
    log.addHandler(file_handler)

    name_formatter = Formatter('%(name)s %(levelname)8s: %(message)s')
    stdout_handler = StreamHandler(stderr if stderr else sys.stderr)
    stdout_handler.setLevel(level(verbosity))
    stdout_handler.setFormatter(name_formatter)
    log.addHandler(stdout_handler)

    clean_old_files(dir, log_unique_expire * 60 * 60 * 24, match_unique, log)

    return log
