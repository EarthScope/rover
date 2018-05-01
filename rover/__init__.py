
from .subscribe import subscribe
from .process import Processes
from .download import download
from .list import list_index
from .ingest import ingest
from .index import index
from .config import RoverArgumentParser, reset_config, RESET_CONFIG, INDEX, MSEEDDB, MSEEDDIR, INGEST, LIST_INDEX, \
    RETRIEVE, HELP, SUBSCRIBE, DOWNLOAD
from .logs import init_log
from .help import help


def execute(command, args, log):
    if not command or command == HELP:
        help(args, log)
    elif command == RESET_CONFIG:
        reset_config(args, log)
    elif command == INDEX:
        index(args, log)
    elif command == INGEST:
        ingest(args, log)
    elif command == LIST_INDEX:
        list_index(args, log)
    elif command == DOWNLOAD:
        download(args, log)
    elif command == SUBSCRIBE:
        subscribe(args, log)
    else:
        raise Exception('Unknown command %s' % command)


def main():
    log, args = None, None
    try:
        argparse = RoverArgumentParser()
        args = argparse.parse_args()
        log = init_log(args.log_dir, args.log_size, args.log_count, args.log_verbosity, args.verbosity, 'rover')
        log.debug('args: %s' % args)
        processes = Processes(args.mseed_db, log)
        if not args.daemon:
            processes.assert_singleton('rover')
        try:
            execute(args.command, args, log)
        finally:
            processes.remove_process()
    except Exception as e:
        if log:
            log.error(str(e))
            if not args or args.dev:
                raise e
        else:
            raise e
