import ctypes
import datetime
import time
import re
import codecs

from binascii import hexlify
from hashlib import sha1
from os import makedirs, stat, getpid, listdir, unlink, kill, name, rename, rmdir, strerror
from os.path import dirname, exists, isdir, expanduser, abspath, join, realpath, getmtime
from shutil import move, copyfile
from subprocess import Popen, check_output, STDOUT
from sys import version_info

if version_info[0] >= 3:
    from os import replace

from requests import __version__ as requests_version, Session
from requests.adapters import HTTPAdapter


"""
Assorted utilities.
"""


def create_parents(path):
    """
    Make sure that the directories in the path exist.
    """
    dir = dirname(path)
    if not exists(dir):
        makedirs(dir)
    if not isdir(dir):
        raise Exception('"%s" is not a directory' % dir)


def touch(path):
    """
    Create or 'modify' a file.
    """
    create_parents(path)
    open(path, 'a').close()


def safe_unlink(path):
    """
    Delete a file if it exists.
    """
    if path is not None and exists(path):
        try:
            unlink(path)
        except PermissionError:
            pass  # file still in use on windows


def check_cmd(config, param, name):
    """
    Check the command exists and, if not, inform the user.
    """
    from .args import FORCECMD
    value = config.arg(param)
    if windows() and '/' in value:
        config.log.warn('Replacing slashes with back-slashes in "%s"' % value)
        value = re.sub(r'/', r'\\', value)
    if not config.arg(FORCECMD):
        cmd = '%s -h' % value
        try:
            check_output(cmd, stderr=STDOUT, shell=True)
            return value
        except Exception as e:
            config.log.error('Command "%s" failed' % cmd)
            config.log.error('Install %s or configure %s correctly' % (name, param))
            raise Exception('Cannot find %s (using %s)' % (name, cmd))
    else:
        config.log.warn('Not checking command %s' % name)
        return value


def canonify(path):
    """
    Expand the path so it's repeatable.
    """
    return realpath(abspath(expanduser(path)))


def canonify_dir_and_make(path):
    """
    We need to canonify and make sure some dirs exist.
    """
    path = canonify(path)
    if not exists(path):
        makedirs(path)
    if not isdir(path):
        raise Exception('%s is not a directory')
    return path


def run(cmd, log, uncouple=False):
    """
    We can't use subprocess.run() because it doesn't exist for 2.7.
    """
    log.debug('Running "%s"' % cmd)
    if uncouple:
        if version_info[0] >= 3:
            Popen(cmd, shell=True, close_fds=True, start_new_session=True)
        else:
            Popen(cmd, shell=True, close_fds=True)
    else:
        process = Popen(cmd, shell=True)
        process.wait()
        if process.returncode:
            raise Exception('Command "%s" failed' % cmd)


def hash(text):
    """
    SHA1 hash as hex.
    """
    hash = sha1()
    hash.update(text.encode('utf-8'))
    return hexlify(hash.digest()).decode('ascii')


def uniqueish(prefix, salt, pid=None):
    """
    Generate a unique(ish) name, from a prefix, text (hashed) and pid.
    """
    if pid is None:
        pid = getpid()
    return '%s_%s_%d' % (prefix, hash(salt)[:6], pid)


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


def unique_path(dir, filename, salt):
    """
    Generate a unique path to a temporary file.
    """
    name = uniqueish(filename, salt)
    return unique_filename(join(dir, name))

def _stream_output(request, down, unique=True):
    # special case empty return.  this avoids handling empty files elsewhere
    # which isn't a 'serious' problem, but causes ugly logging
    if request.status_code == 204:
        return None, lambda: None
    else:
        down = canonify(down)
        create_parents(down)
        if unique:
            down = unique_filename(down)
        with open(down, 'wb') as output:
            for chunk in request.iter_content(chunk_size=1024):
                if chunk:
                    output.write(chunk)
        return down, request.raise_for_status


def _session(retries):
    """
    Ugliness required by requests lib to set max retries.
    (We don't really care about efficiency to the point where we need to re-use the session)
    """
    # https://stackoverflow.com/questions/21371809/cleanly-setting-max-retries-on-python-requests-get-or-post-method
    session = Session()
    http_adapter = HTTPAdapter(max_retries=retries)
    https_adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', http_adapter)
    session.mount('https://', https_adapter)

    # Create a User-Agent header with package, requests and Python identifiers
    from rover import __version__
    user_agent = 'rover/%s python-requests/%s Python/%s' % \
                 (__version__, requests_version, ".".join(map(str, version_info[:3])))
    session.headers.update({'User-Agent': user_agent})

    return session


def get_to_file(url, down, timeout, retries, log, unique=True):
    """
    Execute an HTTP GET request, with output to a file.

    Returns (path, lambda)
    where path is the path to the file (possibly None if no data downloaded)
          lambda() (ie when called) will raise an exception on HTTP error
    this gives the caller both the results (which may contain error msg)
    and the error exception.
    """
    log.info('Downloading %s from %s' % (down, url))
    request = _session(retries).get(url, stream=True, timeout=timeout)
    return _stream_output(request, down, unique=unique)


def post_to_file(url, up, down, timeout, retries, log, unique=True):
    """
    Execute an HTTP POST request, with output to a file.

    Returns (path, lambda)
    where path is the path to the file (possibly None if no data downloaded)
          lambda() (ie when called) will raise an exception on HTTP error
    this gives the caller both the results (which may contain error msg)
    and the error exception.
    """
    up = canonify(up)
    log.info('Downloading %s from %s with %s' % (down, url, up))
    with open(up, 'rb') as input:
        request = _session(retries).post(url, stream=True, data=input, timeout=timeout)
    return _stream_output(request, down, unique=unique)


def clean_old_files(dir, age_secs, match, log):
    """
    Delete old files that match the predicate.
    """
    if exists(dir):
        for file in listdir(dir):
            if match(file):
                try:
                    if time.time() - getmtime(file) > age_secs:
                        log.warn('Deleting old %s' % file)
                except:   # py2.7 no FileNotFound
                    pass  # was deleted from under us


def match_prefixes(*prefixes):
    """
    Match predicate (see above) using a prefix.
    """
    def match(name):
        for prefix in prefixes:
            if name.startswith(prefix):
                return True
        return False
    return match


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


ZERO = datetime.timedelta(0)


class UTC(datetime.tzinfo):
    """UTC timezone (needed for Py2.7)"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


utc = UTC()
EPOCH = datetime.datetime.utcfromtimestamp(0)
EPOCH_UTC = EPOCH.replace(tzinfo=utc)


def assert_valid_time(log, time):
    """
    Check timestamp format.
    """
    if re.match(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?)?$', time):
        return time
    else:
        msg = 'Invalid time format "%s"' % time
        log.error(msg)
        raise Exception(msg)


def format_epoch(epoch):
    """
    Format an epoch in the standard format.
    """
    dt = datetime.datetime.fromtimestamp(epoch, utc)
    return datetime.datetime.strftime(dt, '%Y-%m-%dT%H:%M:%S.%f')


def format_day_epoch(epoch):
    """
    Format an epoch as a date, without time.
    """
    dt = datetime.datetime.fromtimestamp(epoch, utc)
    return datetime.datetime.strftime(dt, '%Y-%m-%d')


def format_year_day_epoch(epoch):
    """
    Format an epoch as year and day
    """
    dt = datetime.datetime.fromtimestamp(epoch, utc)
    return datetime.datetime.strftime(dt, '%Y-%j')


def format_time_epoch(epoch):
    """
    Format an epoch, with time to seconds
    """
    dt = datetime.datetime.fromtimestamp(epoch, utc)
    return datetime.datetime.strftime(dt, '%Y-%m-%dT%H:%M:%S')


def format_time_epoch_local(epoch):
    """
    Format an epoch, with time to seconds
    """
    dt = datetime.datetime.fromtimestamp(epoch)
    return datetime.datetime.strftime(dt, '%Y-%m-%dT%H:%M:%S')


def parse_epoch(date):
    """
    Parse a date in the standard formats
    """
    if date.endswith('Z'):
        date = date[:-1]
    try:
        dt = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        try:
            dt = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            try:
                dt = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M')
            except ValueError:
                dt = datetime.datetime.strptime(date, '%Y-%m-%d')
    return (dt - EPOCH).total_seconds()


def tidy_timestamp(log, timestamp):
    try:
        tidied = format_epoch(parse_epoch(timestamp))
        if tidied != timestamp:
            log.debug('Tidied timestamp: "%s" -> "%s"' % (timestamp, tidied))
        return tidied
    except:
        msg = 'Cannot parse timestamp "%s"' % timestamp
        log.error(msg)
        raise Exception(msg)


def in_memory(iterator):
    """
    Pull an entire iterator into memory and then re-expose as an iterator.
    """
    return iter(list(iterator))


STATION = 'station'
NETWORK = 'network'
CHANNEL = 'channel'
LOCATION = 'location'


def build_file(log, path, args):
    """
    Given a N_S_L_C or net=... and start/end times, construct an input file in
    the correct (availability service) format.
    """
    # just go crazy because any error is caught by the caller and changed into a 'bad syntax' error
    if '_' in args[0]:
        (n, s, l, c) = (code if code else '--' for code in args[0].split('_'))
        args = ['net=' + n, 'sta=' + s, 'loc=' + l, 'cha=' + c] + args[1:]
    sncl = {NETWORK: '*', STATION: '*', LOCATION: '*', CHANNEL: '*'}
    count = 0
    while args and '=' in args[0]:
        arg = args.pop(0)
        name, value = arg.split('=')
        for key in sncl.keys():
            if key.startswith(name):
                sncl[key] = value
                count += 1
    assert count
    assert len(args) < 3
    parts = [sncl[NETWORK], sncl[STATION], sncl[LOCATION], sncl[CHANNEL]]
    parts += args
    with open(path, 'w') as req:
        print(' '.join(parts), file=req)


def sort_file_inplace(log, path, temp_dir, sort_in_python):
    """
    Sort file using UNIX command line utility.
    """
    done = False
    try:
        if not sort_in_python:
            _os_sort(log, path, temp_dir)
            done = True
    except Exception as e:
        log.warn('OS sorting failed (%s) using python fallback' % e)
    if not done:
        _python_sort(log, path)


def _python_sort(log, path):
    log.debug('Sorting %s in memory' % path)
    with open(path, 'r') as source:
        lines = source.readlines()
    with open(path, 'w') as dest:
        for line in sorted(lines):
            print(line.rstrip(), file=dest)


def _os_sort(log, path, temp_dir):
    sorted_path = unique_path(temp_dir, 'rover_sort', path)
    log.debug('Sorting %s into %s' % (path, sorted_path))
    run('sort %s > %s' % (path, sorted_path), log)
    safe_unlink(path)
    move(sorted_path, path)


def process_exists(pid):
    """
    Check whether the given PID exists.
    """
    if windows():
        # https://stackoverflow.com/questions/17620833/check-if-pid-exists-on-windows-with-python-without-requiring-libraries
        kernel32 = ctypes.windll.kernel32
        process = kernel32.OpenProcess(0x100000, 0, pid)
        if process:
            kernel32.CloseHandle(process)
            return True
        else:
            return False
    else:
        try:
            kill(pid, 0)
            return True
        except OSError:
            return False


def windows():
    """
    Are we running on windows?
    """
    return name in ('Windows', 'nt')


def diagnose_error(log, error, request, response, copied=True):
    # avoid import loop
    from .args import mm, VERBOSITY, NO, DELETEFILES
    log.error(error)
    log.error('Response contents (max 10 lines) are listed below:')
    log_file_contents(response, log, 10)
    log.error('Please pay special attention to the first lines of the message - ' +
              'they often contains useful information.')
    log.error('Request contents (max 10 lines) are listed below:')
    log_file_contents(request, log, 10)
    log.error('The request is either provided by the user or created from the user input.')
    if copied:
        log.error('To ensure consistency ROVER copies files.  ' +
                  'To see the paths and avoid deleting temporary copies re-run the command ' +
                  'with the %s 5 and %s%s options' % (mm(VERBOSITY), NO, DELETEFILES))


def log_file_contents(path, log, max_lines=10):
    log.info('Displaying contents of file %s:' % path)
    count = 0
    try:
        with codecs.open(path, encoding='utf-8', errors='strict') as input:
            for line in input:
                line = line.strip()
                if line:
                    log.error('> %s' % line)
                    count += 1
                    if count >= max_lines:
                        break
    except UnicodeDecodeError:
        log.error('File contents are not printable.')
    except IOError as e:
        log.error('Error opening file:', strerror(e.errno))


def calc_bytes(sizestring):
    """
    Calculate a size in bytes for the specified size string.  If the
    string is terminated with the following suffixes the specified
    scaling will be applied:

    'K' or 'k' : kilobytes - value * 1024
    'M' or 'm' : megabytes - value * 1024*1024
    'G' or 'g' : gigabytes - value * 1024*1024*1024

    Returns a size in bytes.
    """

    if sizestring.endswith('k') or sizestring.endswith('K'):
        return int(sizestring[:-1]) * 1024

    elif sizestring.endswith('m') or sizestring.endswith('M'):
        return int(sizestring[:-1]) * 1024 * 1024

    elif sizestring.endswith('g') or sizestring.endswith('G'):
        return int(sizestring[:-1]) * 1024 * 1024 * 1024

    else:
        return int(sizestring)


def null_fixer(log, line):
    return line


def iris_fixer(log, line):
    """
    Tidy and validate a request file line as used by the retrieve command.

    Empty lines and lines beginning with '#' are considered acceptable, but
    should not be submitted to a web service.

    Return the tidied request line on success.

    Return None on acceptable line that should not be included in a service request.

    Raise exception for unacceptable lines.
    """
    line = line.strip()

    if len(line) == 0:
        return None

    if line.startswith('#'):
        return None

    fields = line.split()

    if len(fields) != 6:
        raise Exception ("Unrecognized request line, not enough fields: '%s'" % line)

    # Acceptable source identifier codes contain only these characters
    acceptable_code = "[-_,A-Za-z0-9*?]"

    if not re.match(acceptable_code, fields[0]):
        raise Exception ("Unrecognized request line, invalid network code: '%s'" % line)

    if not re.match(acceptable_code, fields[1]):
        raise Exception ("Unrecognized request line, invalid station code: '%s'" % line)

    if not re.match(acceptable_code, fields[2]):
        raise Exception ("Unrecognized request line, invalid location code: '%s'" % line)

    if not re.match(acceptable_code, fields[3]):
        raise Exception ("Unrecognized request line, invalid channel code: '%s'" % line)

    # Tidy time values, allowing '*' as an exception (meaning "open" time)
    if fields[4] != '*':
        try:
            fields[4] = tidy_timestamp(log, fields[4])
        except:
            raise Exception ("Unrecognized request line, invalid start time: '%s'" % line)

    if fields[5] != '*':
        try:
            fields[5] = tidy_timestamp(log, fields[5])
        except:
            raise Exception ("Unrecognized request line, invalid end time: '%s'" % line)

    return " ".join(fields)


def fix_file_inplace(log, path, temp_dir, fixer=iris_fixer):
    temp_path = unique_path(temp_dir, 'rover_fixed_request', path)
    log.debug('Fixing %s in %s' % (path, temp_path))
    try:
        with open(temp_path, 'w') as output:
            with open(path, 'r') as input:
                for line in input.readlines():
                    line = line.rstrip()  # remove linefeed
                    line = fixer(log, line)
                    if line:
                        print(line, file=output)
        unlink(path)
        log.debug('Replacing %s with %s' % (path, temp_path))
        copyfile(temp_path, path)
    finally:
        safe_unlink(temp_path)


def atomic_move(log, src, dest):
    '''
    This uses an atomic primitive in 3.3+ and on unix.
    On Windows the best we can do is two operations, repeating if we catch an interrupt.
    https://bugs.python.org/issue8828
    '''
    if version_info[0] >= 3:
        log.debug('Moving %s to %s (atomic 3)' % (src, dest))
        replace(src, dest)
    else:
        if windows():
            log.debug('Moving %s to %s (windows)' % (src, dest))
            exception = None
            while exists(src):
                try:
                    safe_unlink(dest)
                    rename(src, dest)
                except KeyboardInterrupt as e:
                    log.debug('Caught interrupt; will re-throw once move complete')
                    exception = e
            if exception:
                raise exception
        else:
            log.debug('Moving %s to %s (atomic 2.7)' % (src, dest))
            rename(src, dest)


def remove_empty_folders(path, log):
    'Function to remove empty folders under root directory'
    if not isdir(path):
        return

    # remove empty subfolders
    files = listdir(path)
    if len(files):
        for f in files:
            fullpath = join(path, f)
            if isdir(fullpath):
                remove_empty_folders(fullpath, log)

    # if folder empty, delete it
    files = listdir(path)
    if len(files) == 0:
        log.debug("Removing empty folder: %s" % path)
        rmdir(path)

def dictionary_text_list(kwargs, prefix=""):
    cmds = []
    for command in kwargs.keys():
        cmds.append("  {0}{1:19}: {2}".format(prefix,
                                              command,
                                              kwargs[command][1]))
    return "\n".join(cmds)
