

from .sqlite import SqliteSupport


class Subscriber(SqliteSupport):

    def __init__(self, db, log):
        super().__init__(db, log)

    def subscribe(self):
        raise Exception('implement subscriber')



def subscribe(core):
    subscriber = Subscriber(core.db, core.log)
    subscriber.subscribe()
