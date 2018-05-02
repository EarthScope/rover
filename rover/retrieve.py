
from os import unlink
from os.path import join, exists
from re import match

from .utils import uniqueish, create_parents, canonify
from .config import RETRIEVE
from .sqlite import SqliteSupport


RETRIEVEFILE = 'rover_retrieve'


class Retriever(SqliteSupport):

    def __init__(self, dbpath, log):
        super().__init__(dbpath, log)

    def retrieve(self, file):
        file = canonify(file)
        if not exists(file):
            raise Exception('Cannot find file %s' % file)
        raise Exception('implement retriever')


def assert_valid_time(time):
    if match(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?)?$', time):
        return time
    else:
        raise Exception('Invalid time format "%s"' % time)


def build_file(temp_dir, sncl, begin, end=None):
    parts = list(sncl.split('.'))
    if len(parts) != 4:
        raise Exception('SNCL "%s" does not have 4 components' % sncl)
    parts.append(assert_valid_time(begin))
    if end:
        parts.append(assert_valid_time(end))
    name = uniqueish(RETRIEVEFILE, sncl)
    path = join(canonify(temp_dir), name)
    create_parents(path)
    with open(path, 'w') as req:
       print(*parts, file=req)
    return path


def retrieve(args, log):
    retriever = Retriever(args.mseed_db, log)
    if len(args.args) == 1:
        retriever.retrieve(args.args[0])
    elif len(args.args) == 0 or len(args.args) > 3:
        raise Exception('Usage: rover %s (file|sncl begin [end])' % RETRIEVE)
    else:
        path = build_file(args.temp_dir, *args.args)
        try:
            retriever.retrieve(path)
        finally:
            unlink(path)


