import os
import sys
import signal
import traceback
from traceback import print_exc

from .logs import LoggingContext
from .process import ProcessManager
from .config import Config

from rover import COMMANDS, HELP_CMD, INIT_REPOSITORY, ABORT_CODE, ERROR_CODE, DEV
from rover import PREV_HANDLER


def execute(command, config):
    from .help import Helper   # avoid import loop
    from .args import Arguments
    if not command:
        # print welcome message and exit
        Arguments().print_help()
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
