
from tempfile import TemporaryDirectory
from os.path import join

from rover.args import Arguments


def test_write_config():
    with TemporaryDirectory() as dir:
        config = join(dir, '.rover')
        argparse = Arguments()
        args = argparse.parse_args(['-f', config])
        assert args.file == config
        with open(config, 'r') as input:
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
# tolerance for overlapping timespans
timespan-tol=0.1
# number of download instances to run
download-workers=10
# allow multiple processes (internal use only)?
multiprocess=False
# command to run rover
rover-cmd=rover
# index before retrieval?
pre-index=True
# call compact after retrieval?
post-compact=True
# availability service url
availability-url=http://service.iris.edu/irisws/availability/1/query
# dataselect service url
dataselect-url=http://service.iris.edu/fdsnws/dataselect/1/query
# temporary storage for downloads
temp-dir=~/rover/tmp
# number of days before deleting temp files
temp-expire=1
# call compact after ingest?
compact=False
# detect and list files with duplicate data?
compact-list=False
# allow duplicate data in mixed data types?
compact-mixed-types=False
# allow compact to mutate (replace) data?
compact-mutate=False
# process all files (not just modified)?
all=False
# when given a directory, process children?
recurse=True
# directory for logs
log-dir=~/rover/logs
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
mseed-db=~/rover/index.sql
# root of mseed data dirs
mseed-dir=~/rover/mseed
# number of mseedindex instances to run
mseed-workers=10
# use leapseconds file?
leap=True
# number of days before refreshing file
leap-expire=30
# file for leapsecond data
leap-file=~/rover/leap-seconds.lst
# URL for leapsecond data
leap-url=http://www.ietf.org/timezones/data/leap-seconds.list
''', contents


def test_enable_daemon():
    argparse = Arguments()
    args = argparse.parse_args(['--daemon'])
    assert args.daemon


def test_disable_daemon():
    with TemporaryDirectory() as dir:
        config = join(dir, '.rover')
        with open(config, 'w') as output:
            output.write('daemon=True\n')
        # first test that config file enables daemons
        argparse = Arguments()
        args = argparse.parse_args(['-f', config])
        assert args.daemon
        # and then test that we can override that
        argparse = Arguments()
        args = argparse.parse_args(['-f', config, '--no-daemon'])
        assert not args.daemon


def test_multiple_flags():
    argparse = Arguments()
    args = argparse.parse_args(['--daemon', '--no-daemon'])
    assert not args.daemon
