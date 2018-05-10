
import datetime
from os import unlink, makedirs
from os.path import join, exists
from re import match
from shutil import copyfile
from sqlite3 import OperationalError

from .args import RETRIEVE
from .compact import Compacter
from .config import NewConfig
from .coverage import SingleSNCLBuilder, Coverage
from .download import DownloadManager
from .index import Indexer
from .sqlite import SqliteSupport
from .utils import uniqueish, canonify, post_to_file, unique_filename, run, check_cmd, clean_old_files, \
    match_prefixes, check_leap, parse_epoch, SingleUse

RETRIEVEFILE = 'rover_retrieve'
EARLY = datetime.datetime(1900, 1, 1)


class Retriever(SqliteSupport, SingleUse):
    """
    Call the availability service, compare with the index, and
    then call the DownloadManager to retrieve the missing data
    (which are ingested and indexed by the Downloader).
    """

    def __init__(self, config):
        SqliteSupport.__init__(self, config)
        SingleUse.__init__(self)
        args = config.args
        self._download_manager = DownloadManager(config)
        self._temp_dir = canonify(args.temp_dir)
        self._availability_url = args.availability_url
        self.timespan_tol = args.timespan_tol
        self._pre_index = args.pre_index
        self._post_compact = args.post_compact
        self._config = config
        # leap seconds not used here, but avoids multiple threads all downloading later
        check_leap(args.leap, args.leap_expire, args.leap_file, args.leap_url, self._log)
        clean_old_files(self._temp_dir, args.temp_expire * 60 * 60 * 24, match_prefixes(RETRIEVEFILE), self._log)

    def query(self, up):
        """
        Retrieve the data specified in the given file (format as for
        availability service) and compare with the index.  Afterwards, call either
        fetch() or display().
        """
        self._assert_single_use()
        if self._pre_index:
            self._log.info('Ensuring index is current before retrieval')
            Indexer(self._config).run([])

        self._prepend_options(up)
        down = self._post_availability(up)
        try:
            self._sort_availability(down)
            for remote in self._parse_availability(down):
                self._log.debug('Available data: %s' % remote)
                local = self._scan_index(remote.sncl)
                self._log.debug('Local data: %s' % local)
                self._request_download(remote.subtract(local))
        finally:
            unlink(down)

    def fetch(self):
        result = self._download_manager.download()
        if self._post_compact:
            self._log.info('Checking for duplicate data')
            Compacter(NewConfig(self._config, all=True, compact_list=True)).run([])
        return result


    def display(self):
        return self._download_manager.display()

    def _prepend_options(self, up):
        tmp = temp_path(self._temp_dir, up)
        self._log.debug('Prepending options to %s via %s' % (up, tmp))
        try:
            with open(tmp, 'w') as output:
                print('mergequality=true', file=output)
                print('mergesamplerate=true', file=output)
                with open(up, 'r') as input:
                    print(input.readline(), file=output, end='')
            unlink(up)
            copyfile(tmp, up)
        finally:
            unlink(tmp)

    def _post_availability(self, up):
        down = temp_path(self._temp_dir, up)
        return post_to_file(self._availability_url, up, down, self._log)

    def _sort_availability(self, down):
        tmp = temp_path(self._temp_dir, down)
        try:
            self._log.debug('Sorting %s via %s' % (down, tmp))
            run('sort %s > %s' % (down, tmp), self._log)  # todo - windows
            unlink(down)
            copyfile(tmp, down)
        finally:
            unlink(tmp)

    def _parse_line(self, line):
        n, s, l, c, b, e = line.split()
        return "%s.%s.%s.%s" % (n, s, l, c), parse_epoch(b), parse_epoch(e)

    def _parse_availability(self, down):
        with open(down, 'r') as input:
            availability = None
            for line in input:
                if not line.startswith('#'):
                    sncl, b, e = self._parse_line(line)
                    if availability and not availability.sncl == sncl:
                        yield availability
                        availability = None
                    if not availability:
                        availability = Coverage(self.timespan_tol, sncl)
                    availability.add_epochs(b, e)
            if availability:
                yield availability

    def _scan_index(self, sncl):
        # todo - we could maybe use time range from initial query?  or from availability?
        availability = SingleSNCLBuilder(self.timespan_tol, sncl)
        def callback(row):
            availability.add_timespans(row[0])
        try:
            self.foreachrow('''select timespans
                                    from tsindex 
                                    where network=? and station=? and location=? and channel=?
                                    order by starttime, endtime''',
                            sncl.split('.'),
                            callback, quiet=True)
        except OperationalError:
            self._log.debug('No index - first time using rover?')
        return availability.coverage()

    def _request_download(self, missing):
        self._log.debug('Data to download: %s' % missing)
        self._download_manager.add(missing)


def temp_path(temp_dir, text):
    """
    Generate a unique path to a temporary file.
    """
    name = uniqueish(RETRIEVEFILE, text)
    return unique_filename(join(temp_dir, name))


def assert_valid_time(time):
    """
    Check timestamp format.
    """
    if match(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?)?$', time):
        return time
    else:
        raise Exception('Invalid time format "%s"' % time)


def build_file(path, sncl, begin, end=None):
    """
    Given a SNCL and begin.end dates, construct an input file in
    the correct (availability service) format.
    """
    parts = list(sncl.split('.'))
    if len(parts) != 4:
        raise Exception('SNCL "%s" does not have 4 components' % sncl)
    parts.append(assert_valid_time(begin))
    if end:
        parts.append(assert_valid_time(end))
    with open(path, 'w') as req:
       print(*parts, file=req)


def retrieve(config, fetch):
    """
    Implement the retrieve command - download data that is available and
    that we don't already have.
    """
    # check these two comands so we fail early
    args = config.args
    check_cmd('%s -h' % args.rover_cmd, 'rover', 'rover', config.log)
    check_cmd('%s -h' % args.mseed_cmd, 'mseedindex', 'mseed-cmd', config.log)
    temp_dir = canonify(args.temp_dir)
    if not exists(temp_dir):
        makedirs(temp_dir)
    retriever = Retriever(config)
    if len(args.args) == 0 or len(args.args) > 3:
        raise Exception('Usage: rover %s (file|sncl begin [end])' % RETRIEVE)
    else:
        # guarantee always called with temp file because we prepend options
        path = temp_path(temp_dir, args.args[0])
        try:
            if len(args.args) == 1:
                copyfile(args.args[0], path)
            else:
                build_file(path, *args.args)
            retriever.query(path)
            if fetch:
                return retriever.fetch()
            else:
                return retriever.display()
        finally:
            unlink(path)
