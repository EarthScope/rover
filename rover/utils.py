
from os.path import dirname, exists, isdir
from os import makedirs


def create_parents(path):
    dir = dirname(path)
    if not exists(dir):
        makedirs(dir)
    if not isdir(dir):
        raise Exception('"%s" is not a directory' % dir)
