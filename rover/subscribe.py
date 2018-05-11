

from .sqlite import SqliteSupport


"""
The 'rvoer subscribe' command.
"""


class Subscriber(SqliteSupport):
    """"
### Subscribe

    rover subscribe

    """

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        raise Exception('implement subscriber')


