
from .args import RESET_CONFIG, INDEX, INGEST, LIST_INDEX, \
    RETRIEVE, HELP, SUBSCRIBE, DOWNLOAD, COMPARE, COMPACT
from .compact import Compacter
from .config import Config, ConfigResetter
from .download import Downloader
from .index import Indexer
from .ingest import Ingester
from .list import IndexLister
from .process import Processes
from .retrieve import Retriever, Comparer
from .subscribe import Subscriber


COMMANDS = {
    RESET_CONFIG: ConfigResetter,
    INDEX: Indexer,
    INGEST: Ingester,
    LIST_INDEX: IndexLister,
    DOWNLOAD: Downloader,
    RETRIEVE: Retriever,
    COMPARE: Comparer,
    COMPACT: Compacter,
    SUBSCRIBE: Subscriber
}


def execute(command, config):
    from .help import Helper   # avoid import loop
    if not command:
        command = 'help'
    commands = dict(COMMANDS)
    commands[HELP] = Helper
    if command in commands:
        commands[command](config).run(config.args.args)
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
