
from os.path import join, dirname
from sys import version_info

if version_info[0] >= 3:
    from tempfile import TemporaryDirectory
else:
    from backports.tempfile import TemporaryDirectory

from rover.config import BaseConfig, RepoInitializer
from rover.args import Arguments, TEMPDIR, DATADIR, FILE, INIT_REPOSITORY, DEFAULT_FILE
from rover.utils import canonify, windows

from .test_utils import WindowsTemp


class DummyLog:

    def debug(self, *args): pass
    def info(self, *args): pass
    def default(self, *args): pass
    def warn(self, *args): pass
    def error(self, *args): pass
    def critical(self, *args): pass


def test_write_config():
    with WindowsTemp(TemporaryDirectory) as dir:
        argparse = Arguments()
        args, config_path = argparse.parse_args([INIT_REPOSITORY])
        config = BaseConfig(DummyLog(), None, args, None, dir)
        RepoInitializer(config).run([dir])
        path = config.file(FILE)
        with open(path, 'r') as input:
            contents = input.read()
            assert contents == \
'''# specify configuration file
file=rover.config
# development mode (show exceptions)?
dev=False
# delete temporary files?
delete-files=True
# display help in markdown format?
md-format=False
# force cmd use (dangerous)
force-cmd=False
# the data directory - data, timeseries.sqlite
data-dir=data
# fractional tolerance for overlapping timespans
timespan-tol=1.5
# maximum number of attempts to download data
download-retries=3
# number of download instances to run
download-workers=5
# command to run rover
rover-cmd=rover
# index before retrieval?
pre-index=True
# call ingest after retrieval?
ingest=True
# call index after ingest?
index=True
# call summary after retrieval?
post-summary=True
# availability service url
availability-url=http://service.iris.edu/irisws/availability/1/query
# dataselect service url
dataselect-url=http://service.iris.edu/fdsnws/dataselect/1/query
# temporary storage for downloads
temp-dir=tmp
# number of days before deleting temp files
temp-expire=1
# timeout for HTTP requests
http-timeout=60
# max retries for HTTP requests
http-retries=3
# force failures for testing (dangerous)
force-failures=0
# avoid OS sort (slower)?
sort-in-python=False
# process all files (not just modified)?
all=False
# when given a directory, process children?
recurse=True
# directory for subscriptions
subscriptions-dir=subscriptions
# time between availabilty checks
recheck-period=12
# skip overlap checks (dangerous)?
force-request=False
# directory for logs
log-dir=logs
# unique log names (with PIDs)?
log-unique=False
# number of days before deleting unique logs
log-unique-expire=7
# log verbosity (0-6)
log-verbosity=4
# maximum log size (1-10)
log-size=6
# maximum number of logs
log-count=10
# console verbosity (0-6)
verbosity=4
# mseedindex command
mseedindex-cmd=mseedindex -sqlitebusyto 60000
# number of mseedindex instances to run
mseedindex-workers=10
# use leapseconds file?
leap=True
# number of days before refreshing file
leap-expire=30
# file for leapsecond data
leap-file=leap-seconds.list
# URL for leapsecond data
leap-url=http://www.ietf.org/timezones/data/leap-seconds.list
# auto-start the download progress web server?
web=True
# bind address for HTTP server
http-bind-address=127.0.0.1
# port for HTTP server
http-port=8000
# address for completion status
email=
# from address for email
email-from=noreply@rover
# address of SMTP server
smtp-address=localhost
# port for SMTP server
smtp-port=25
''', contents


def test_multiple_flags():
    argparse = Arguments()
    args, config_path = argparse.parse_args(['--index', '--no-index'])
    assert not args.index


def test_CONFIGDIR_start():
    with WindowsTemp(TemporaryDirectory) as dir:
        config = join(dir, DEFAULT_FILE)
        with open(config, 'w') as output:
            output.write('temp-dir=${CONFIGDIR}/foo\n')
            output.write('data-dir=$${CONFIGDIR}/foo\n')
        argparse = Arguments()
        args, config_path = argparse.parse_args(['-f', config])
        config = BaseConfig(None, None, args, None, dirname(config_path))
        assert config.dir(TEMPDIR)
        assert config.dir(TEMPDIR) == canonify(dir + '/foo'), config.dir(TEMPDIR)
        assert config.dir(DATADIR)
        assert config.dir(DATADIR) == canonify(join(dir, '${CONFIGDIR}/foo')), config.dir(DATADIR)


def test_CONFIGDIR_middle():
    if not windows():  # gets confused over messed up path
        with WindowsTemp(TemporaryDirectory) as dir:
            dir = canonify(dir)
            config = join(dir, '.rover')
            with open(config, 'w') as output:
                output.write('temp-dir=xx${CONFIGDIR}/foo\n')
                output.write('data-dir=xx$${CONFIGDIR}/foo\n')
            argparse = Arguments()
            args, config_path = argparse.parse_args(['-f', config])
            config = BaseConfig(None, None, args, None, dirname(config_path))
            assert config.dir(TEMPDIR)
            assert config.dir(TEMPDIR) == canonify(join(dir, 'xx' + dir + '/foo')), config.dir(TEMPDIR)
            assert config.dir(DATADIR)
            assert config.dir(DATADIR) == canonify(join(dir, 'xx${CONFIGDIR}/foo')), config.dir(DATADIR)


def test_CONFIGDIR_bad():
    with WindowsTemp(TemporaryDirectory) as dir:
        config = join(dir, '.rover')
        with open(config, 'w') as output:
            output.write('temp-dir=${FOO}\n')
        argparse = Arguments()
        args, config_path = argparse.parse_args(['-f', config])
        config = BaseConfig(None, None, args, None, dirname(config_path))
        try:
            config.arg(TEMPDIR)
        except Exception as e:
            assert 'does not exist' in str(e), str(e)
        else:
            assert False, 'Expected exception'
