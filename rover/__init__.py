
from .config import Config, reset_config
from .args import RESET_CONFIG, INDEX, INGEST, LIST_INDEX, \
    RETRIEVE, HELP, SUBSCRIBE, DOWNLOAD, COMPARE
from .download import download
from .help import help
from .index import index
from .ingest import ingest
from .list import list_index
from .process import Processes
from .retrieve import retrieve
from .subscribe import subscribe


def execute(command, config):
    if not command or command == HELP:
        help(config.args)
    elif command == RESET_CONFIG:
        reset_config(config)
    elif command == INDEX:
        index(config)
    elif command == INGEST:
        ingest(config)
    elif command == LIST_INDEX:
        list_index(config)
    elif command == DOWNLOAD:
        download(config)
    elif command in (RETRIEVE, COMPARE):
        retrieve(config, command == RETRIEVE)
    elif command == SUBSCRIBE:
        subscribe(config)
    else:
        raise Exception('Unknown command %s' % command)


def main():
    config = None
    try:
        config = Config()
        processes = Processes(config)
        if not (config.args.daemon or config.args.multiprocess):
            processes.assert_singleton('rover')
        try:
            execute(config.args.command, config)
        finally:
            processes.remove_process()
    except Exception as e:
        if config and config.log:
            config.log.error(str(e))
            if not config or not config.args or config.args.dev:
                raise e
        else:
            raise e
