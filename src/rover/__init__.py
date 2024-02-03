pkg_path = __file__

# the following replaces the default signal handler so that keyboardinterrupt
# is not raised if the user hits ctrl-C
# the value 2 matches ABORT_CODE in rover.args, but we want to do this before
# importing any other module.  see issue 46.

import signal
import sys
from collections import OrderedDict
from itertools import chain
from .__version__ import __version__


def signal_handler(sig, frame):
    sys.exit(2)


PREV_HANDLER = signal.signal(signal.SIGINT, signal_handler)

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
COMMON_COMMANDS[LIST_RETRIEVE] = (ListRetriever, 'Show what data "rover retrieve" will download')
COMMON_COMMANDS[LIST_INDEX] = (IndexLister, 'List the contents of the repository')
COMMON_COMMANDS[LIST_SUMMARY] = (SummaryLister, 'List a summary of the repository')
# so that help appears in the docs
COMMON_COMMANDS[HELP_CMD] = (None, 'Return help information about a command')

ADVANCED_COMMANDS = OrderedDict()
ADVANCED_COMMANDS[DOWNLOAD] = (Downloader, 'Download data from a remote service')
ADVANCED_COMMANDS[INDEX] = (Indexer, 'Index the repository')
ADVANCED_COMMANDS[INGEST] = (Ingester, 'Ingest data from a file into the repository')
ADVANCED_COMMANDS[WEB] = (ServerStarter, 'Start a web server showing status')
ADVANCED_COMMANDS[RETRIEVE_METADATA] = (MetadataRetriever, 'Download missing metadata')
ADVANCED_COMMANDS[SUMMARY] = (Summarizer, 'Update summary table')
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
