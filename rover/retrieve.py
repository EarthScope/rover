

from .sqlite import SqliteSupport


class Retriever(SqliteSupport):

    def __init__(self, dbpath, log):
        super().__init__(dbpath, log)

    def retrieve(self):
        raise Exception('implement retriever')



def retrieve(args, log):
    retriever = Retriever(args.mseed_dir, args.log)
    retriever.retrieve()
