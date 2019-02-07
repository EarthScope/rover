
import sys
from io import StringIO
from logging import getLogger, StreamHandler, Formatter, DEBUG, addLevelName
from logging.handlers import RotatingFileHandler
from os import makedirs, getpid
from os.path import join, exists, isdir
from re import match

from .utils import clean_old_files, canonify, calc_bytes

"""
Support for logging.
"""

DEFAULT = 25   # a new logging level, between INFO and WARN


def level(n):
    '''
    Our log levels are 0-6 (silent - verbose).
    Logging levels are 50-10 (quiet - verbose)

    Ours        Logging
    0  None     60
    1  Critical 50
    2  Error    40
    3  Warning  30
    4  Default  25
    5  Info     20
    6  Debug    10

    '''
    n = max(0, min(n, 6))
    if n == 4:
        return 25
    elif n < 4:
        return 60 - 10 * n
    else:
        return 70 - 10 * n


def match_unique(name):
    return match(r'\w+_\d+\.log', name)


def log_name(log_dir, name):
    dir = canonify(log_dir)
    if not exists(dir):
        makedirs(dir)
    if not isdir(dir):
        raise Exception('"%s" is not a directory (log-dir)' % dir)
    path = join(dir, name + '.log')
    return path, dir


def init_log(log_dir, log_size, log_count, log_verbosity, verbosity, name, log_unique, log_unique_expire, stderr=None):
    """
    Create a log with two handlers.
    One handler is a rotated file, the other stderr.
    The file is for details, stderr for errors to the user.
    """

    addLevelName(DEFAULT, 'DEFAULT')

    if log_unique:
        name = '%s.%d' % (name, getpid())

    log = getLogger(name)
    log.setLevel(DEBUG)

    if log_dir:  # on initialization we have no log dir
        path, dir = log_name(log_dir, name)
        size = calc_bytes (log_size)
        count = max(min(log_count, 100), 1)
        file_handler = RotatingFileHandler(path, maxBytes=size, backupCount=count)
        stream = None
    else:
        stream = StringIO()
        file_handler = StreamHandler(stream)
        path, dir = None, None

    time_formatter = Formatter('%(levelname)-8s %(asctime)s: %(message)s')
    file_handler.setFormatter(time_formatter)
    file_handler.setLevel(level(log_verbosity))
    log.addHandler(file_handler)

    name_formatter = Formatter('%(name)s %(levelname)8s: %(message)s')
    stdout_handler = StreamHandler(stderr if stderr else sys.stderr)
    stdout_handler.setLevel(level(verbosity))
    stdout_handler.setFormatter(name_formatter)
    log.addHandler(stdout_handler)

    if dir:
        clean_old_files(dir, log_unique_expire * 60 * 60 * 24, match_unique, log)

    def get_file_handler():
        return file_handler
    
    def get_stdout_handler():
        return stdout_handler

    log.get_file_handler = get_file_handler
    log.get_stdout_handler = get_stdout_handler

    # monkey patch logger (LogAdapter works in 3, but fails on 2)
    def default(msg, *args, **kwargs):
        log.log(DEFAULT, msg, *args, **kwargs)

    log.default = default

    if dir:
        clean_old_files(dir, log_unique_expire * 60 * 60 * 24, match_unique, log)

    return log, path, stream


class LoggingContext(object):
    """
    Use this context manager to temporarily change the logging configuration
    and revert it back after doing something.
    """

    def __init__(self, logger, level=None, handler=None, close=True):
        self.logger = logger
        self.level = level
        self.handler = handler
        self.close = close

    def __enter__(self):
        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)
        if self.handler:
            self.old_handlers = self.logger.handlers
            self.logger.handlers = []
            self.logger.addHandler(self.handler)

    def __exit__(self, et, ev, tb):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.handler:
            self.logger.handlers = self.old_handlers
        if self.handler and self.close:
            self.logger.handlers = self.old_handlers
            self.handler.close()
        # implicit return of None => don't swallow exceptions
