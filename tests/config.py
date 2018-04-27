
from rover.config import RoverArgumentParser
from tempfile import TemporaryDirectory
from os.path import join


def test_write_config():
    with TemporaryDirectory() as dir:
        config = join(dir, '.rover')
        argparse = RoverArgumentParser()
        args = argparse.parse_args(['-f', config])
        assert args.file == config
        with open(config, 'r') as input:
            contents = input.read()
            assert contents == \
'''# use background processes?
daemon=False
# development mode (show exceptions)?
dev=False
# use leapseconds file?
leap=True
# number of days before refreshing file
leap-expire=30
# file for leapsecond data
leap-file=~/rover/leap-seconds.lst
# URL for leapsecond data
leap-url=http://www.ietf.org/timezones/data/leap-seconds.list
# directory for logs
log-dir=~/rover/logs
# log verbosity (0-5)
log-verbosity=5
# maximum log size (1-10)
log-size=6
# maximum number of logs
log-count=10
# mseedindex command
mseed-cmd=mseedindex
# mseedindex database (also used by rover)
mseed-db=~/rover/index.sql
# root of mseed data dirs
mseed-dir=~/rover/mseed
# number of mseedindex instances to run
mseed-workers=10
# temporary storage for downloads
temp-dir=~/rover/tmp
# stdout verbosity (0-5)
verbosity=4
''', contents


def test_enable_daemon():
    argparse = RoverArgumentParser()
    args = argparse.parse_args(['--daemon'])
    assert args.daemon


def test_disable_daemon():
    with TemporaryDirectory() as dir:
        config = join(dir, '.rover')
        with open(config, 'w') as output:
            output.write('daemon=True\n')
        # first test that config file enables daemons
        argparse = RoverArgumentParser()
        args = argparse.parse_args(['-f', config])
        assert args.daemon
        # and then test that we can override that
        argparse = RoverArgumentParser()
        args = argparse.parse_args(['-f', config, '--no-daemon'])
        assert not args.daemon


def test_multiple_flags():
    argparse = RoverArgumentParser()
    args = argparse.parse_args(['--daemon', '--no-daemon'])
    assert not args.daemon
