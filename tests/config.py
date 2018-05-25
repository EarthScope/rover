
from os.path import join
from sys import version_info

from rover.config import BaseConfig

if version_info[0] >= 3:
    from tempfile import TemporaryDirectory
else:
    from backports.tempfile import TemporaryDirectory

from rover.args import Arguments, TEMPDIR, MSEEDDIR, FILE_
from rover.utils import canonify


def test_write_config():
    with TemporaryDirectory() as dir:
        path = join(dir, '.rover')
        argparse = Arguments()
        args, configdir = argparse.parse_args(['-f', path])
        config = BaseConfig(None, args, None, configdir)
        assert canonify(config.arg(FILE_)) == canonify(path), config.arg(FILE_)
        with open(path, 'r') as input:
            contents = input.read()
            assert contents == \
'''# use background processes?
daemon=False
# development mode (show exceptions)?
dev=False
# delete temporary files?
delete-files=True
# display help in markdown format?
md-format=False
# directory for subscriptions
subscriptions-dir=subscriptions
# fractional tolerance for overlapping timespans
timespan-tol=1.5
# number of download instances to run
download-workers=10
# allow multiple processes (internal use only)?
multiprocess=False
# command to run rover
rover-cmd=rover
# index before retrieval?
pre-index=True
# call ingest after retrieval?
ingest=True
# call index after ingest?
index=True
# availability service url
availability-url=http://service.iris.edu/irisws/availability/1/query
# dataselect service url
dataselect-url=http://service.iris.edu/fdsnws/dataselect/1/query
# temporary storage for downloads
temp-dir=tmp
# number of days before deleting temp files
temp-expire=1
# process all files (not just modified)?
all=False
# when given a directory, process children?
recurse=True
# directory for logs
log-dir=logs
# base file name for logs
log-name=rover
# unique log names (with PIDs)?
log-unique=False
# number of days before deleting unique logs
log-unique-expire=7
# log verbosity (0-5)
log-verbosity=5
# maximum log size (1-10)
log-size=6
# maximum number of logs
log-count=10
# console verbosity (0-5)
verbosity=4
# mseedindex command
mseed-cmd=mseedindex
# mseedindex database (also used by rover)
mseed-db=index.sql
# root of mseed data dirs
mseed-dir=mseed
# number of mseedindex instances to run
mseed-workers=10
# use leapseconds file?
leap=True
# number of days before refreshing file
leap-expire=30
# file for leapsecond data
leap-file=leap-seconds.lst
# URL for leapsecond data
leap-url=http://www.ietf.org/timezones/data/leap-seconds.list
''', contents


def test_enable_daemon():
    argparse = Arguments()
    args, configdir = argparse.parse_args(['--daemon'])
    assert args.daemon


def test_disable_daemon():
    with TemporaryDirectory() as dir:
        config = join(dir, '.rover')
        with open(config, 'w') as output:
            output.write('daemon=True\n')
        # first test that config file enables daemons
        argparse = Arguments()
        args, configdir = argparse.parse_args(['-f', config])
        assert args.daemon
        # and then test that we can override that
        argparse = Arguments()
        args, configdir = argparse.parse_args(['-f', config, '--no-daemon'])
        assert not args.daemon


def test_multiple_flags():
    argparse = Arguments()
    args, configdir = argparse.parse_args(['--daemon', '--no-daemon'])
    assert not args.daemon


# todo - need config instance, not just args

def test_CONFIGDIR_start():
      with TemporaryDirectory() as dir:
        config = join(dir, '.rover')
        with open(config, 'w') as output:
            output.write('temp-dir=${CONFIGDIR}/foo\n')
            output.write('mseed-dir=$${CONFIGDIR}/foo\n')
        argparse = Arguments()
        args, configdir = argparse.parse_args(['-f', config])
        config = BaseConfig(None, args, None, configdir)
        assert config.dir_path(TEMPDIR)
        assert config.dir_path(TEMPDIR) == canonify(dir + '/foo'), config.dir_path(TEMPDIR)
        assert config.dir_path(MSEEDDIR)
        assert config.dir_path(MSEEDDIR) == join(dir, '${CONFIGDIR}/foo'), config.dir_path(MSEEDDIR)

def test_CONFIGDIR_middle():
      with TemporaryDirectory() as dir:
        dir = canonify(dir)
        config = join(dir, '.rover')
        with open(config, 'w') as output:
            output.write('temp-dir=xx${CONFIGDIR}/foo\n')
            output.write('mseed-dir=xx$${CONFIGDIR}/foo\n')
        argparse = Arguments()
        args, configdir = argparse.parse_args(['-f', config])
        config = BaseConfig(None, args, None, configdir)
        assert config.dir_path(TEMPDIR)
        assert config.dir_path(TEMPDIR) == join(dir, 'xx' + dir + '/foo'), config.dir_path(TEMPDIR)
        assert config.dir_path(MSEEDDIR)
        assert config.dir_path(MSEEDDIR) == join(dir, 'xx${CONFIGDIR}/foo'), config.dir_path(MSEEDDIR)

def test_CONFIGDIR_bad():
      with TemporaryDirectory() as dir:
        config = join(dir, '.rover')
        with open(config, 'w') as output:
            output.write('temp-dir=${FOO}\n')
        argparse = Arguments()
        args, configdir = argparse.parse_args(['-f', config])
        config = BaseConfig(None, args, None, configdir)
        try:
            config.arg(TEMPDIR)
        except Exception as e:
            assert 'does not exist' in str(e), str(e)
        else:
            assert False, 'Expected exception'
