
from .config import Arguments, reset_config, RESET_CONFIG, INDEX, INGEST, LIST_INDEX, \
    RETRIEVE, HELP, SUBSCRIBE, DOWNLOAD, COMPARE
from .download import download
from .help import help
from .index import index
from .ingest import ingest
from .list import list_index
from .logs import init_log
from .process import Processes
from .retrieve import retrieve
from .sqlite import init_db
from .subscribe import subscribe


def execute(command, core):
    if not command or command == HELP:
        help(core.args, core.log)
    elif command == RESET_CONFIG:
        reset_config(core)
    elif command == INDEX:
        index(core)
    elif command == INGEST:
        ingest(core)
    elif command == LIST_INDEX:
        list_index(core)
    elif command == DOWNLOAD:
        download(core)
    elif command in (RETRIEVE, COMPARE):
        retrieve(core, command==RETRIEVE)
    elif command == SUBSCRIBE:
        subscribe(core)
    else:
        raise Exception('Unknown command %s' % command)


class Core:

    def __init__(self):
        argparse = Arguments()
        self.args = argparse.parse_args()
        self.log = init_log(self.args.log_dir, self.args.log_size, self.args.log_count, self.args.log_verbosity,
                            self.args.verbosity, self. args.log_name, self.args.log_unique, self.args.log_unique_expire)
        self.log.debug('Args: %s' % self.args)
        self.db = init_db(self.args.mseed_db, self.log)


def main():
    core = None
    try:
        core = Core()
        processes = Processes(core.db, core.log)
        if not (core.args.daemon or core.args.multiprocess):
            processes.assert_singleton('rover')
        try:
            execute(core.args.command, core)
        finally:
            processes.remove_process()
    except Exception as e:
        if core and core.log:
            core.log.error(str(e))
            if not core or not core.args or core.args.dev:
                raise e
        else:
            raise e
