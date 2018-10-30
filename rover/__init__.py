
pkg_path = __file__
__version__ = '0.0.8plus'

# the following replaces the default signal handler so that keyboardinterrupt
# is not raised if the user hits ctrl-C
# the value 2 matches ABORT_CODE in rover.args, but we want to do this before
# importing any other module.  see issue 46.

import signal
import sys

def signal_handler(sig, frame):
    sys.exit(2)

signal.signal(signal.SIGINT, signal_handler)


from traceback import print_exc

from .args import INIT_REPOSITORY, INDEX, INGEST, LIST_INDEX, \
    RETRIEVE, HELP, SUBSCRIBE, DOWNLOAD, LIST_RETRIEVE, START, STOP, LIST_SUBSCRIBE, UNSUBSCRIBE, DAEMON, \
    DEV, SUMMARY, LIST_SUMMARY, STATUS, WEB, TRIGGER, ABORT_CODE, ERROR_CODE
from .config import Config, RepoInitializer
from .daemon import Starter, Stopper, Daemon, StatusShower
from .download import Downloader
from .index import Indexer, IndexLister
from .ingest import Ingester
from .process import ProcessManager
from .retrieve import Retriever, ListRetriever
from .subscribe import Subscriber, SubscriptionLister, Unsubscriber, Trigger
from .summary import Summarizer, SummaryLister
from .web import ServerStarter


COMMANDS = {
    INIT_REPOSITORY: (RepoInitializer, 'Create / configure the repository'),
    INDEX: (Indexer, 'Index the repository'),
    INGEST: (Ingester, 'Ingest data from a file into the repository'),
    SUMMARY: (Summarizer, 'Update summary table'),
    LIST_INDEX: (IndexLister, 'List the contents of the repository'),
    LIST_SUMMARY: (SummaryLister, 'List a summary of the repository'),
    DOWNLOAD: (Downloader, 'Download data from a remote service'),
    RETRIEVE: (Retriever, 'Download, ingest and index missing data'),
    LIST_RETRIEVE: (ListRetriever, 'Show what data "rover retrieve" will download'),
    START: (Starter, 'Start the background daemon'),
    STOP: (Stopper, 'Stop the background daemon'),
    STATUS: (StatusShower, 'Show the background daemon status'),
    DAEMON: (Daemon, 'The background daemon (prefer start/stop)'),
    SUBSCRIBE: (Subscriber, 'Add a subscription'),
    LIST_SUBSCRIBE: (SubscriptionLister, 'List the subscriptions'),
    TRIGGER: (Trigger, 'Ask the daemon to reprocess subscriptions'),
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
        try:
            config = Config()
            if config.command and config.command != HELP:
                config.lazy_validate()
            # initialise without a database...
            if not config.command or config.command in (INIT_REPOSITORY, HELP):
                execute(config.command, config)
            else:
                with ProcessManager(config):
                    execute(config.command, config)
        except KeyboardInterrupt:
            exit(ABORT_CODE)
    except Exception as e:
        if config and config.log:
            config.log.critical(str(e))
            if config.command in COMMANDS:
                config.log.default('See "rover help %s"' % config.command)
            elif config.command != HELP:
                config.log.default('See "rover help help" for a list of commands')
            if not config or not config._args or config.arg(DEV):
                print_exc()
        else:
            print_exc()
        # use an exit code so that workers are detected as failing
        exit(ERROR_CODE)
