
from binascii import hexlify
from hashlib import sha1
from os.path import dirname, exists, isdir, expanduser, abspath
from os import makedirs, stat
from subprocess import Popen, check_output, STDOUT
from time import time
from urllib.request import urlretrieve


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
        raise Exception('Cannot find %s' % name)


def canonify(path):
    """
    Expand the path so it's repeatable.
    """
    return abspath(expanduser(path))


def run(cmd, log):
    """
    We can't use subprocess.run() because it doesn't exist for 2.7.
    """
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
            log.info('Downloading %s from %s' % (file, url))
            urlretrieve(url, file)
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


def lastmod(path):
    """
    The last modified epoch for the file.
    """
    statinfo = stat(path)
    return statinfo.st_atime


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

