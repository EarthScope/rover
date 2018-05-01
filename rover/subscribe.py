

from .sqlite import SqliteSupport


class Subscriber(SqliteSupport):

    def __init__(self, dbpath, log):
        super().__init__(dbpath, log)

    def subscribe(self):
        raise Exception('implement subscriber')



def subscribe(args, log):
    subscriber = Subscriber(args.mseed_dir, args.log)
    subscriber.subscribe()
