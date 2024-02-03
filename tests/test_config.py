import pytest
from tempfile import TemporaryDirectory
from os.path import join, dirname

from rover.config import BaseConfig, RepoInitializer
from rover.args import Arguments, TEMPDIR, DATADIR, FILE, INIT_REPOSITORY, DEFAULT_FILE
from rover.utils import canonify, windows

class DummyLog:
    def debug(self, *args): pass
    def info(self, *args): pass
    def default(self, *args): pass
    def warn(self, *args): pass
    def error(self, *args): pass
    def critical(self, *args): pass


def test_write_config(tmp_path):

    argparse = Arguments()
    args, config_path = argparse.parse_args([INIT_REPOSITORY])

    with TemporaryDirectory() as dir:
        config = BaseConfig(DummyLog(), None, args, None, dir)
        RepoInitializer(config).run([dir])

        path = config.file(FILE)
        dirpath = dirname(path)
        with open(path, 'r') as input:
            contents = input.read()
            assert contents == \
                '''# the data directory - data, timeseries.sqlite
data-dir='''+dirpath+'''/data
# maximum number of attempts to download data
download-retries=3
# number of download instances to run
download-workers=5
# output data format. Choose from "mseed" (miniSEED) or "asdf" (ASDF)
output-format=mseed
# name of ASDF file when ASDF output is specified
asdf-filename=asdf.h5
# station service url
station-url=http://service.iris.edu/fdsnws/station/1/query
# availability service url
availability-url=http://service.iris.edu/fdsnws/availability/1/query
# dataselect service url
dataselect-url=http://service.iris.edu/fdsnws/dataselect/1/query
# temporary storage for downloads
temp-dir='''+dirpath+'''/tmp
# directory for logs
log-dir='''+dirpath+'''/logs
# log verbosity (0-6)
log-verbosity=4
# console verbosity (0-6)
verbosity=4
# auto-start the download progress web server?
web=True
# port for HTTP server
http-port=8000
# address for completion status
email=
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
    with TemporaryDirectory() as dir:
        config = join(dir, DEFAULT_FILE)
        with open(config, 'w') as output:
            output.write('temp-dir=${CONFIGDIR}/foo\n')
            output.write('data-dir=$${CONFIGDIR}/foo\n')

        argparse = Arguments()
        args, config_path = argparse.parse_args(['-f', config])
        config = BaseConfig(None, None, args, None, dirname(config_path))

        assert config.dir(TEMPDIR)
        assert config.dir(TEMPDIR) == canonify(str(dir) + '/foo'), config.dir(TEMPDIR)
        assert config.dir(DATADIR)
        assert config.dir(DATADIR) == canonify(str(dir) + canonify(dir) + '/foo'), config.dir(DATADIR)


def test_CONFIGDIR_middle(tmp_path):
    with TemporaryDirectory() as dir:
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
        assert config.dir(DATADIR) == canonify(dir + '/xx' + canonify(dir) + '/foo'), config.dir(DATADIR)


def test_CONFIGDIR_bad():
    with TemporaryDirectory() as dir:
        config = join(dir, '.rover')
        with open(config, 'w') as output:
            output.write('temp-dir=${FOO}\n')
        argparse = Arguments()
        args, config_path = argparse.parse_args(['-f', config])
        try:
            config = BaseConfig(None, None, args, None, dirname(config_path))
            config.arg(TEMPDIR)
        except Exception as e:
            assert 'does not exist' in str(e), str(e)
        else:
            assert False, 'Expected exception'
