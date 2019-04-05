
pkg_path = __file__

# the following replaces the default signal handler so that keyboardinterrupt
# is not raised if the user hits ctrl-C
# the value 2 matches ABORT_CODE in rover.args, but we want to do this before
# importing any other module.  see issue 46.

import os
import signal
import sys
import traceback
from collections import OrderedDict
from itertools import chain

# Set __version__ from package VERSION file
version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
with open(version_file, "r") as vf:
    __version__ = vf.read().strip()


def signal_handler(sig, frame):
    sys.exit(2)

PREV_HANDLER = signal.signal(signal.SIGINT, signal_handler)


from traceback import print_exc

from .args import INIT_REPOSITORY, INDEX, INGEST, LIST_INDEX, \
    RETRIEVE, RETRIEVE_METADATA, HELP_CMD, SUBSCRIBE, DOWNLOAD, LIST_RETRIEVE, \
    START, STOP, LIST_SUBSCRIBE, UNSUBSCRIBE, DAEMON, \
    DEV, SUMMARY, LIST_SUMMARY, STATUS, WEB, TRIGGER, ABORT_CODE, ERROR_CODE
from .config import Config, RepoInitializer
from .daemon import Starter, Stopper, Daemon, StatusShower
from .download import Downloader
from .index import Indexer, IndexLister
from .ingest import Ingester
from .logs import LoggingContext
from .process import ProcessManager
from .retrieve import Retriever, ListRetriever
from .retrieve_metadata import MetadataRetriever
from .subscribe import Subscriber, SubscriptionLister, Unsubscriber, Trigger
from .summary import Summarizer, SummaryLister
from .web import ServerStarter

COMMON_COMMANDS = OrderedDict()
COMMON_COMMANDS[INIT_REPOSITORY] = (RepoInitializer, 'Create / configure the repository')
COMMON_COMMANDS[RETRIEVE] = (Retriever, 'Download, ingest and index missing data')
COMMON_COMMANDS[LIST_INDEX] = (IndexLister, 'List the contents of the repository')
COMMON_COMMANDS[LIST_RETRIEVE] = (ListRetriever, 'Show what data "rover retrieve" will download')
COMMON_COMMANDS[LIST_SUMMARY] = (SummaryLister, 'List a summary of the repository')
COMMON_COMMANDS[SUMMARY] = (Summarizer, 'Update summary table')
# so that help appears in the docs
COMMON_COMMANDS[HELP_CMD] = (None, 'Return help information about a command.')

ADVANCED_COMMANDS = OrderedDict()
ADVANCED_COMMANDS[DOWNLOAD] = (Downloader, 'Download data from a remote service')
ADVANCED_COMMANDS[INDEX] = (Indexer, 'Index the repository')
ADVANCED_COMMANDS[INGEST] = (Ingester, 'Ingest data from a file into the repository')
ADVANCED_COMMANDS[WEB] = (ServerStarter, 'Start a web server showing status')
ADVANCED_COMMANDS[RETRIEVE_METADATA] = (MetadataRetriever, 'Download missing metadata')
#ADVANCED_COMMANDS[START] = (Starter, 'Start the background daemon')
#ADVANCED_COMMANDS[STOP] = (Stopper, 'Stop the background daemon')
#ADVANCED_COMMANDS[STATUS] = (StatusShower, 'Show the background daemon status')
#ADVANCED_COMMANDS[DAEMON] = (Daemon, 'The background daemon (prefer start/stop)')
#ADVANCED_COMMANDS[SUBSCRIBE] = (Subscriber, 'Add a subscription')
#ADVANCED_COMMANDS[LIST_SUBSCRIBE] = (SubscriptionLister, 'List the subscriptions')
#ADVANCED_COMMANDS[TRIGGER] = (Trigger, 'Ask the daemon to reprocess subscriptions')
#ADVANCED_COMMANDS[UNSUBSCRIBE] = (Unsubscriber, 'Remove subscriptions')


COMMANDS = OrderedDict(chain(COMMON_COMMANDS.items(),
                             ADVANCED_COMMANDS.items()))


def execute(command, config):
    from .help import Helper   # avoid import loop
    from .args import welcome
    if not command:
        # print welcome message and exit
        Helper(config).print_help(welcome())
        return
    commands = dict(COMMANDS)
    commands[HELP_CMD] = (Helper, '')
    if command in commands:
        commands[command][0](config).run(config.args)
    else:
        raise Exception('Unknown command %s' % command)


def main():
    config = None
    try:
        try:
            # reset the old handler now that we can catch keyboardinterrupt
            # this is necessary for windows / 2.7 where copies are not atomic and we need to catch this
            # (and it generally seems like a good idea - let's try not to change how python works too much)
            signal.signal(signal.SIGINT, PREV_HANDLER)
            config = Config()
            if config.command and config.command != HELP_CMD:
                config.lazy_validate()
            # initialise without a database...
            if not config.command or config.command in (INIT_REPOSITORY, HELP_CMD):
                execute(config.command, config)
            else:
                with ProcessManager(config):
                    execute(config.command, config)
        except KeyboardInterrupt:
            exit(ABORT_CODE)
    except Exception as e:
        if config and config.log:
            # log short error message to stdout and stack trace to a file
            with LoggingContext(config.log, handler=config.log.get_stdout_handler()):
                config.log.critical(str(e))
            with LoggingContext(config.log, handler=config.log.get_file_handler()):
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error_traceback = "".join(traceback.format_exception(exc_type,
                                                                     exc_value,
                                                                     exc_traceback))
                config.log.critical(error_traceback)
            if config.command in COMMANDS:
                config.log.default('See "rover {} {}"'.format(HELP_CMD,
                                                              config.command))
            elif config.command != HELP_CMD:
                config.log.default('See "rover {}" for a list of commands'
                                   .format(HELP_CMD))
            if not config or not config._args or config.arg(DEV):
                print_exc()
        else:
            print_exc()
        # use an exit code so that workers are detected as failing
        exit(ERROR_CODE)
