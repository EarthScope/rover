
from tempfile import TemporaryDirectory
from tempfile import mktemp

from os.path import join

from rover.retrieve import Retriever
from rover import init_log
from test_utils import find_root, assert_files, open_db


def test_retrieve():
    root = find_root()
    with TemporaryDirectory() as dir:
        log = init_log(dir, 7, 1, 5, 0, 'test')
        dbpath = mktemp(dir=dir)
        retriever = Retriever(dbpath, dir, join(root, '..', 'mseedindex', 'mseedindex'),
                              dir, False, None, None, None, 1, log)
        retriever.retrieve('http://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2010-02-27T06:30:00.000&end=2010-02-27T10:30:00.000')
        assert_files(join(dir, 'IU'), '2010')
        assert_files(join(dir, 'IU', '2010'), '58')
        assert_files(join(dir, 'IU', '2010', '58'), 'ANMO.IU.2010.58')
        db = open_db(dbpath)
        n = db.cursor().execute('select count(*) from tsindex').fetchone()[0]
        assert n == 1, n  # todo is this right?  just one?
