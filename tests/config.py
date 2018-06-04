
from os.path import join
from sys import version_info

from rover.config import BaseConfig

if version_info[0] >= 3:
    from tempfile import TemporaryDirectory
else:
    from backports.tempfile import TemporaryDirectory

from rover.args import Arguments, TEMPDIR, MSEEDDIR, FILE
from rover.utils import canonify


def test_write_config():
    with TemporaryDirectory() as dir:
        path = join(dir, '.rover')
        argparse = Arguments()
        args, configdir = argparse.parse_args(['-f', path])
        config = BaseConfig(None, None, args, None, configdir)
        assert canonify(config.arg(FILE)) == canonify(path), config.arg(FILE)
        with open(path, 'r') as input:
            contents = input.read()
            assert contents == \
'''# development mode (show exceptions)?
dev=False
# delete temporary files?
delete-files=True
# display help in markdown format?
md-format=False
# the local store - mseed data, index.sql
mseed-dir=mseed
# fractional tolerance for overlapping timespans
timespan-tol=1.5
# number of download instances to run
download-workers=10
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
# log verbosity (0-5)
log-verbosity=5
# maximum log size (1-10)
log-size=6
# maximum number of logs
log-count=10
# console verbosity (0-5)
verbosity=4
# mseedindex command
mseedindex-cmd=mseedindex
# number of mseedindex instances to run
mseedindex-workers=10
# use leapseconds file?
leap=True
# number of days before refreshing file
leap-expire=30
# file for leapsecond data
leap-file=leap-seconds.lst
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
    args, configdir = argparse.parse_args(['--index', '--no-index'])
    assert not args.index


def test_CONFIGDIR_start():
      with TemporaryDirectory() as dir:
        config = join(dir, '.rover')
        with open(config, 'w') as output:
            output.write('temp-dir=${CONFIGDIR}/foo\n')
            output.write('mseed-dir=$${CONFIGDIR}/foo\n')
        argparse = Arguments()
        args, configdir = argparse.parse_args(['-f', config])
        config = BaseConfig(None, None, args, None, configdir)
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
        config = BaseConfig(None, None, args, None, configdir)
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
        config = BaseConfig(None, None, args, None, configdir)
        try:
            config.arg(TEMPDIR)
        except Exception as e:
            assert 'does not exist' in str(e), str(e)
        else:
            assert False, 'Expected exception'
