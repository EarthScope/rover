

from .sqlite import SqliteSupport


"""
The 'rvoer subscribe' command.
"""


class Subscriber(SqliteSupport):

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        raise Exception('implement subscriber')



def subscribe(config):
    """
    Implement the subscribe command - TODO
    """
    Subscriber(config).run(config.args.args)
