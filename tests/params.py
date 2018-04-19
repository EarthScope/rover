
from rover.params import RoverArgumentParser
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
'''# use background processes
daemon=False
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
