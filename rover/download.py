
import datetime
from os import getpid
from os.path import join, exists
from time import time

from .args import DOWNLOAD, MULTIPROCESS, LOGNAME, LOGUNIQUE, mm, DEV, Arguments
from .ingest import Ingester
from .sqlite import SqliteSupport
from .utils import canonify, uniqueish, get_to_file, check_cmd, unique_filename, \
    clean_old_files, match_prefixes, PushBackIterator, utc, EPOCH_UTC, format_epoch, format_day_epoch, SingleUse, \
    create_parents, unique_path, canonify_dir_and_make, safe_unlink
from .workers import Workers

"""
The 'rover download' command - download data from a URL (and then call ingest).

(and the DownloadManager buffer that 'rover retrieve' calls, which spawns multiple Downloaders). 
"""


# if a download process fails or hangs, we need to clear out
# the file, so use a specific name and check for old files
# in the download area
TMPFILE = 'rover_tmp_download'
CONFIGFILE = 'rover_config'


class Downloader(SqliteSupport, SingleUse):
    """
### Download

    rover download url [path]

Download a single request (typically for a day) to teh given path, ingest and index it.  If no path is given then
a temporary file is created and deleted after use.

The url should be for a Data Select service, and should not request data that spans multiple calendar days.

##### Significant Parameters

@temp-dir
@delete-files
@ingest
@compact
@index
@verbosity
@log-dir
@log-name
@log-verbosity

In addition, parameters for sub-commands (ingest, index, and possibly compact) will be used - see help for those
commands for more details.

##### Examples

    rover download \\
    http://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2010-02-27T06:30:00.000&end=2010-02-27T10:30:00.000

will download, ingest and index data from the given URL..

    rover download http://.... --compact

will download, ingest and index data from the given URL and remove duplicate data from the store.

"""

# The only complex thing here is that these may run in parallel.  That means that
# multiple ingest instances can be running in parallel, all using  mseedindex.
# To avoid conflict over sqlite access we use a different database file for each,
# so we need to track and delete those.
#
# To do this we have a table that lists ingesters, along with URLs, PIDs,
# database paths and epochs.
#
# This isn't a problem for the main ingest command because only a single instance
# of the command line command runs at any one time.

    def __init__(self, config):
        SqliteSupport.__init__(self, config)
        SingleUse.__init__(self)
        args = config.args
        self._temp_dir = canonify_dir_and_make(args.temp_dir)
        self._delete_files = args.delete_files
        self._blocksize = 1024 * 1024
        self._ingest = args.ingest
        self._config = config
        self._create_ingesters_table()
        clean_old_files(self._temp_dir, args.temp_expire, match_prefixes(TMPFILE, CONFIGFILE), self._log)

    def run(self, args):
        """
        Download the give URL, then call ingest and index before deleting.
        """
        if len(args) < 1 or len(args) > 2:
            raise Exception('Usage: rover %s url [path]' % DOWNLOAD)
        url = args[0]
        if len(args) == 2:
            path, delete = args[2], False
        else:
            path, delete = unique_path(self._temp_dir, TMPFILE, url), True
        self._assert_single_use()
        retrievers_id, db_path = self._update_downloaders_table(url)
        try:
            self._do_download(url, path)
            if self._ingest:
                Ingester(self._config).run([path], db_path=db_path)
        finally:
            if self._delete_files:
                if path and delete:
                    safe_unlink(path)
                safe_unlink(db_path)
                self.execute('delete from rover_ingesters where id = ?', (retrievers_id,))

    def _update_downloaders_table(self, url):
        self._clear_dead_retrievers()
        pid = getpid()
        db_path = self._ingesters_db_path(url, pid)
        self.execute('insert into rover_ingesters (pid, db_path, url) values (?, ?, ?)', (pid, db_path, url))
        id = self.fetchsingle('select id from rover_ingesters where pid = ? and db_path like ? and url like ?',
                              (pid, db_path, url))  # todo - auto retrieve key?
        return id, db_path

    def _clear_dead_retrievers(self):
        if self._delete_files:
            for row in self.fetchall('select id, db_path from rover_ingesters where creation_epoch < ?', (time() - 60 * 60,)):
                id, file = row
                if exists(file):
                    self._log.warn('Forcing deletion of temp database %s' % file)
                    safe_unlink(file)
                self.execute('delete from rover_ingesters where id = ?', (id,))

    def _do_download(self, url, path):
        # previously we extracted the file name from the header, but the code
        # failed in python 2 (looked like a backport library bug), so now we let the user specify,
        if exists(path):
            raise Exception('Path %s for download already exists' % path)
        create_parents(path)
        return get_to_file(url, path, self._log)

    def _create_ingesters_table(self):
        """
        Create the table used by the retriever.  This is here because the
        table may be created by either a retriever or a download manager.
        """
        self.execute('''create table if not exists rover_ingesters (
                           id integer primary key autoincrement,
                           pid integer,
                           db_path text unique,
                           creation_epoch int default (cast(strftime('%s', 'now') as int)),
                           url text not null
                         )''')

    def _ingesters_db_path(self, url, pid):
        name = uniqueish('rover_ingester', url)
        return unique_filename(join(self._temp_dir, name))


class DownloadManager(SingleUse):
    """
    An interface to downloader instances that restricts downloads to a fixed number of workers,
    each downloading data that is for a maximum duration of a day.

    Used in two steps.  First, coverage data are added (via 'add()').  These are expanded to
    timespans that are processed as workers when 'display()' or 'download()' is called.

    This acts as a buffer, soaking up all the requests from the Retriever so that can
    run through the database as quickly as possible, but avoiding expanding that into too
    many timespans (which could consume a lot of memory if the user requests a large
    date range).
    """

    def __init__(self, config):
        super().__init__()
        args, log = config.args, config.log
        self._log = log
        self._dataselect_url = args.dataselect_url
        check_cmd('%s -h' % args.rover_cmd, 'rover', 'rover', log)
        self._rover_cmd = args.rover_cmd
        check_cmd('%s -h' % args.mseed_cmd, 'mseedindex', 'mseed-cmd', log)
        self._mseed_cmd = args.mseed_cmd
        self._temp_dir = canonify_dir_and_make(args.temp_dir)
        self._dev = args.dev
        self._log_unique = args.log_unique
        self._args = args
        self._coverages = []
        self._workers = Workers(config, args.download_workers)
        self._config_path = None

    def add(self, coverage):
        """
        Add a required coverage (SNCL and date range).  This will be expanded
        into one or more downloads when
        """
        self._assert_not_used()
        self._coverages.append(coverage)

    def display(self):
        """
        Display a asummary of the data.
        """
        self._assert_single_use()
        print()
        total_seconds, total_sncls = 0, 0
        for coverage in self._coverages:
            sncl_seconds = 0
            for (begin, end) in coverage.timespans:
                seconds = end - begin
                sncl_seconds += seconds
                total_seconds += seconds
            if sncl_seconds:
                total_sncls += 1
                print('  %s  (%4.2f sec)' % (coverage.sncl, sncl_seconds))
                for (begin, end) in coverage.timespans:
                    print('    %s - %s  (%4.2f sec)' % (format_epoch(begin), format_epoch(end), end - begin))
        if total_sncls:
            print()
        print('  Total: %d SNCLSs; %4.2f sec' % (total_sncls, total_seconds))
        print()
        return total_sncls

    def download(self):
        """
        Expand the timespans into daily downloads, get the data and ingest.
        """
        self._assert_single_use()
        self._config_path = self._write_config()
        n_downloads = 0
        try:
            for coverage in self._coverages:
                for sncl, begin, end in self._expand_timespans(coverage):
                    self._new_worker(sncl, begin, end)
                    n_downloads += 1
        finally:
            self._workers.wait_for_all()
            # no need to kill thread as it is a daemon - ok to leave it blocked on empty queue
            if n_downloads:
                self._log.info('Completed %d downloads' % n_downloads)
            else:
                self._log.warn('No data downloaded / ingested')
            safe_unlink(self._config_path)
        return n_downloads

    def _write_config(self):
        if self._coverages:
            junk = str(self._coverages[0])
        else:
            junk = 'empty'
        path = unique_filename(join(canonify(self._temp_dir), uniqueish(CONFIGFILE, junk)))
        self._log.debug('Writing config to %s' % path)
        Arguments().write_config(path, self._args)
        return path

    def _expand_timespans(self, coverage):
        sncl, timespans = coverage.sncl, PushBackIterator(iter(coverage.timespans))
        for begin, end in timespans:
            if begin == end:
                yield sncl, begin, end
            else:
                left, right = self._end_of_day(begin)
                yield sncl, begin, min(left, end)
                if right < end:
                    timespans.push((right, end))

    def _end_of_day(self, epoch):
        day = datetime.datetime.fromtimestamp(epoch, utc)
        right = (datetime.datetime(day.year, day.month, day.day, tzinfo=utc)
                 + datetime.timedelta(hours=24) - EPOCH_UTC).total_seconds()
        left = right - 0.000001
        return left, right

    def _new_worker(self, sncl, begin, end):
        # we only pass arguments on the command line that are different from the
        # default (which is in the file)
        command = '%s -f \'%s\' %s %s %s %s %s %s \'%s\'' % (
            self._rover_cmd, self._config_path, mm(MULTIPROCESS), mm(LOGNAME), DOWNLOAD,
            mm(LOGUNIQUE) if self._log_unique else '', mm(DEV) if self._dev else '',
            DOWNLOAD, self._build_url(sncl, begin, end))
        self._log.debug(command)
        self._workers.execute(command)

    def _build_url(self, sncl, begin, end):
        url_params = 'net=%s&sta=%s&loc=%s&cha=%s' % tuple(sncl.split('.'))
        return '%s?%s&start=%s&end=%s' % (self._dataselect_url, url_params, format_epoch(begin), format_epoch(end))

