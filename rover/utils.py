
from binascii import hexlify
from hashlib import sha1
from os import makedirs, stat, getpid, listdir
from os.path import dirname, exists, isdir, expanduser, abspath
from subprocess import Popen, check_output, STDOUT
from time import time
from datetime import datetime

from requests import get, post


def create_parents(path):
    """
    Make sure that the directories in the path exist.
    """
    dir = dirname(path)
    if not exists(dir):
        makedirs(dir)
    if not isdir(dir):
        raise Exception('"%s" is not a directory' % dir)


def check_cmd(cmd, name, param, log):
    """
    Check the command exists and, if not, inform the user.
    """
    try:
        check_output(cmd, stderr=STDOUT, shell=True)
    except:
        log.error('Command "%s" failed' % cmd)
        log.error('Install %s or configure %s correctly' % (name, param))
        raise Exception('Cannot find %s (using %s)' % (name, cmd))


def canonify(path):
    """
    Expand the path so it's repeatable.
    """
    return abspath(expanduser(path))


def run(cmd, log):
    """
    We can't use subprocess.run() because it doesn't exist for 2.7.
    """
    log.debug('Running "%s"' % cmd)
    process = Popen(cmd, shell=True)
    process.wait()
    if process.returncode:
        raise Exception('Command "%s" failed' % cmd)


def check_leap(enabled, expire, file, url, log):
    """
    Download a file if none exists or it is more than 3 months old.

    Returns the file name or NONE - the value to be passed to the mseedindex command.
    """
    if enabled:
        file = canonify(file)
        if exists(file):
            statinfo = stat(file)
            age = int(time()) - statinfo.st_atime
            log.debug('%s is %ds old' % (file, age))
            download = age > expire * 24 * 60 * 60
        else:
            download= True
        if download:
            get_to_file(url, file, log, unique=False)
        return file
    else:
        return 'NONE'


def hash(text):
    """
    SHA1 hash as hex.
    """
    hash = sha1()
    hash.update(text.encode('utf-8'))
    return hexlify(hash.digest()).decode('ascii')


def uniqueish(prefix, text, pid=None):
    """
    Generate a unique(ish) name, from a prefix, text (hashed) and pid.
    """
    if pid is None:
        pid = getpid()
    return '%s_%s_%d' % (prefix, hash(text)[:6], pid)


def lastmod(path):
    """
    The last modified epoch for the file.
    """
    statinfo = stat(path)
    return statinfo.st_mtime


def unique_filename(path):
    """
    Append a count until we find a unique name.
    """
    if exists(path):
        count = 0
        while True:
            count += 1
            new_path = '%s.%d' % (path, count)
            if not exists(new_path):
                return new_path
    else:
        return path


def _stream_output(request, down, unique=True):
    down = canonify(down)
    create_parents(down)
    if unique:
        down = unique_filename(down)
    with open(down, 'wb') as output:
        for chunk in request.iter_content(chunk_size=1024):
            if chunk:
                output.write(chunk)
    return down


def get_to_file(url, down, log, unique=True):
    log.info('Downloading %s from %s' % (down, url))
    request = get(url, stream=True)
    return _stream_output(request, down, unique=unique)


def post_to_file(url, up, down, log, unique=True):
    up = canonify(up)
    log.info('Downloading %s from %s with %s' % (down, url, up))
    with open(up, 'rb') as input:
        request = post(url, stream=True, data=input)
    return _stream_output(request, down, unique=unique)


def parse_time(time):
    if time.endswith('Z'):
        time = time[:-1]
    return datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f')


def parse_short_time(time):
    if time.endswith('Z'):
        time = time[:-1]
    return datetime.strptime(time, '%Y-%m-%dT%H:%M:%S')


def format_time(time):
    return datetime.strftime(time, '%Y-%m-%dT%H:%M:%S.%f')


class PushBackIterator:
    """
    Modify an iterator so that a (single) value can be pushed back
    and will be returned next iteration.
    """

    def __init__(self, iter):
        self._iter = iter
        self._pushed = None

    def push(self, value):
        if self._pushed:
            raise Exception('Cannot push multiple values')
        self._pushed = value

    def __iter__(self):
        return self

    def __next__(self):
        if self._pushed:
            value, self._pushed = self._pushed, None
        else:
            value = next(self._iter)
        return value


def clean_old_files(dir, age_secs, match, log):
    if exists(dir):
        for file in listdir(dir):
            if match(file):
                try:
                    if time() - lastmod(file) > age_secs:
                        log.warn('Deleting old %s' % file)
                except FileNotFoundError:
                    pass  # was deleted from under us


def match_prefixes(*prefixes):
    def match(name):
        for prefix in prefixes:
            if name.startswith(prefix):
                return True
        return False
    return match
