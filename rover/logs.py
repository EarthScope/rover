
from logging import getLogger, StreamHandler, Formatter, DEBUG
from logging.handlers import RotatingFileHandler
from os.path import join, exists, isdir, expanduser
from os import makedirs
import sys


def level(n):
    '''
    Our log levels are 0-5 (silent - verbose).
    Logging levels are 50-10 (quiet - verbose)
    '''
    return 10 * (6 - (max(min(n, 5), 0)))


def init_log(log_dir, log_size, log_count, log_verbosity, verbosity, name, stderr=None):
    """
    Create a log with two handlers.
    One handler is a rotated file, the other stderr.
    The file is for details, stderr for errors to the user.
    """

    log = getLogger(name)
    log.setLevel(DEBUG)

    dir = expanduser(log_dir)
    if not exists(dir):
        makedirs(dir)
    if not isdir(dir):
        raise Exception('"%s" is not a directory (log-dir)' % dir)

    time_formatter = Formatter('%(levelname)-8s %(asctime)s: %(message)s')
    path = join(dir, name + '.log')
    # smallest size is 8kB (2^13), largest size 1MB (2^20)
    size = 2 ** (12 + max(min(log_size, 7), 1))
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

    return log
