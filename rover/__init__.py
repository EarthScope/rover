
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
    RESET_CONFIG: (ConfigResetter, 'Reset the configuration'),
    INDEX: (Indexer, 'Index the local store'),
    INGEST: (Ingester, 'Ingest data from a file into the local store'),
    LIST_INDEX: (IndexLister, 'List the contents of the local store'),
    DOWNLOAD: (Downloader, 'Download data from a remote service'),
    RETRIEVE: (Retriever, 'Download, ingest and index missing data'),
    COMPARE: (Comparer, 'Show what data "rover retrieve" will download'),
    COMPACT: (Compacter, 'Detect and remove duplicate data'),
    SUBSCRIBE: (Subscriber, 'TODO')
}


def execute(command, config):
    from .help import Helper   # avoid import loop
    if not command:
        command = 'help'
    commands = dict(COMMANDS)
    commands[HELP] = (Helper, '')
    if command in commands:
        commands[command][0](config).run(config.args.args)
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
            if config.args.command in COMMANDS:
                config.log.info('See "rover help %s"' % config.args.command)
            elif config.args.command != HELP:
                config.log.info('See "rover help help" for a list of commands')
            if not config or not config.args or config.args.dev:
                raise e
        else:
            raise e
