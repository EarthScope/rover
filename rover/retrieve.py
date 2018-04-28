
from sys import version_info
from os import getpid, unlink
from os.path import join
# avoid bug in backport libs for python 2
if version_info[0] < 3:
    from urllib import urlretrieve
else:
    from urllib.request import urlretrieve

from .config import RETRIEVE
from .index import Indexer
from .ingest import MseedindexIngester
from .utils import canonify, create_parents, hash
from .sqlite import SqliteSupport, NoResult


class Retriever(SqliteSupport):
    """
    The only complex thing here is that these may run in parallel
    and call ingest.  That means that multiple ingest instances
    can be running in parallel, all using temp tables in the database.
    So we need to manage temp table names and clear out old tables
    from crashed processes.

    To do this we have another table that is a list of retrievers,
    along with URLs, PIDs, table names and epochs.

    This isn't a problem for the main ingest command because only
    a sin=gle instance of the command line command runs at any one
    time.
    """
    # todo - enforce the single instance condition above

    def __init__(self, dbpath, tmpdir, mseedindex, mseed_dir, leap, leap_expire, leap_file, leap_url, n_workers, log):
        super().__init__(dbpath, log)
        self._tmpdir = canonify(tmpdir)
        self._blocksize = 1024 * 1024
        self._ingester = MseedindexIngester(mseedindex, dbpath, mseed_dir, leap, leap_expire, leap_file, leap_url, log)
        self._indexer = Indexer(mseedindex, dbpath, mseed_dir, n_workers, leap, leap_expire, leap_file, leap_url, log)
        self._load_retrievers_table()

    def retrieve(self, url):
        """
        Download the give URL, then call ingest and index before deleting.
        """
        self._assert_single_use()
        retrievers_id, table = self._update_retrievers_table(url)
        try:
            path = self._do_download(url)
            self._ingester.ingest([path], table=table)
            self._indexer.index()
            unlink(path)
        finally:
            self._execute('drop table if exists %s' % table)
            self._execute('delete from rover_retrievers where id = ?', (retrievers_id,))

    def _update_retrievers_table(self, url):
        self._clear_dead_retrievers()
        # either we already have an entry in the table for our url,
        # in which case url is present and pid is not, or we need
        # to create an entry ourselves.
        try:
            id, pid, table = self._fetchone('select id, pid, table_name from rover_retrievers where url like ?', (url,))
            if pid and pid != getpid():
                raise Exception('A retriever already exists for %s' % url)
            self._execute('update rover_retrievers set pid = ? where id = ?', (getpid(), id))
        except NoResult:
            table = self._retrievers_table_name(url)
            self._execute('insert into rover_retrievers (pid, table_name, url) values (?, ?, ?)', (getpid(), table, url))
            id = self._fetchsingle('select id from rover_retrievers where url like ?', (url,))
        return id, table

    def _do_download(self, url):
        # previously we extracted teh file name from the header, but the code
        # failed in python 2 (looked like a backport library bug), so since
        # the file will be deleted soon anyway we now use an arbitrary name
        path = join(self._tmpdir, hash(url)[1:20])
        create_parents(path)
        urlretrieve(url, filename=path)
        return path


def retrieve(args, log):
    """
    Implement the retrieve command - download, ingest and index data.
    """
    retriever = Retriever(args.mseed_db, args.temp_dir, args.mseed_cmd, args.mseed_dir,
                          args.leap, args.leap_expire, args.leap_file, args.leap_url, args.mseed_workers, log)
    if len(args.args) != 1:
        raise Exception('Provide a single argument (the URL) to %s' % RETRIEVE)
    retriever.retrieve(args.args[0])
