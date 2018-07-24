
import sys
from traceback import print_exc

from .web import ServerStarter
from .args import INIT_REPOSITORY, INDEX, INGEST, LIST_INDEX, \
    RETRIEVE, HELP, SUBSCRIBE, DOWNLOAD, LIST_RETRIEVE, START, STOP, LIST_SUBSCRIBE, UNSUBSCRIBE, DAEMON, \
    DEV, SUMMARY, LIST_SUMMARY, STATUS, WEB, RESUBSCRIBE
from .config import Config, RepoInitializer
from .daemon import Starter, Stopper, Daemon, StatusShower
from .download import Downloader
from .index import Indexer, IndexLister
from .ingest import Ingester
from .process import ProcessManager
from .retrieve import Retriever, ListRetriever
from .subscribe import Subscriber, SubscriptionLister, Unsubscriber, Resubscriber
from .summary import Summarizer, SummaryLister


COMMANDS = {
    INIT_REPOSITORY: (RepoInitializer, 'Configure the local store'),
    INDEX: (Indexer, 'Index the local store'),
    INGEST: (Ingester, 'Ingest data from a file into the local store'),
    SUMMARY: (Summarizer, 'Update summary table'),
    LIST_INDEX: (IndexLister, 'List the contents of the local store'),
    LIST_SUMMARY: (SummaryLister, 'List a summary of the local store'),
    DOWNLOAD: (Downloader, 'Download data from a remote service'),
    RETRIEVE: (Retriever, 'Download, ingest and index missing data'),
    LIST_RETRIEVE: (ListRetriever, 'Show what data "rover retrieve" will download'),
    START: (Starter, 'Start the background daemon'),
    STOP: (Stopper, 'Stop the background daemon'),
    STATUS: (StatusShower, 'Show the background daemon status'),
    DAEMON: (Daemon, 'The background daemon (prefer start/stop)'),
    SUBSCRIBE: (Subscriber, 'Add a subscription'),
    LIST_SUBSCRIBE: (SubscriptionLister, 'List the subscriptions'),
    RESUBSCRIBE: (Resubscriber, 'Ask the daemon to reprocess subscriptions'),
    UNSUBSCRIBE: (Unsubscriber, 'Remove subscriptions'),
    WEB: (ServerStarter, 'Start a web server showing status')
}


def execute(command, config):
    from .help import Helper   # avoid import loop
    if not command:
        command = 'help'
    commands = dict(COMMANDS)
    commands[HELP] = (Helper, '')
    if command in commands:
        commands[command][0](config).run(config.args)
    else:
        raise Exception('Unknown command %s' % command)


def main():
    config = None
    try:
        config = Config()
        config.lazy_validate()
        # initialise without a database...
        if config.command == INIT_REPOSITORY:
            execute(config.command, config)
        else:
            with ProcessManager(config):
                execute(config.command, config)
    except Exception as e:
        if config and config.log:
            config.log.critical(str(e))
            if config.command in COMMANDS:
                config.log.info('See "rover help %s"' % config.command)
            elif config.command != HELP:
                config.log.info('See "rover help help" for a list of commands')
            if not config or not config._args or config.arg(DEV):
                print_exc()
        else:
            print_exc()
        # use an exit code so that workers are detected as failing
        exit(1)
