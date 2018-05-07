

from .sqlite import SqliteSupport


class Subscriber(SqliteSupport):

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        raise Exception('implement subscriber')



def subscribe(config):
    Subscriber(config).run(config.args.args)
