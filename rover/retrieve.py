
import datetime
from os import unlink, makedirs
from os.path import exists
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
from .utils import canonify, post_to_file, run, check_cmd, clean_old_files, \
    match_prefixes, check_leap, parse_epoch, SingleUse, unique_path


"""
The 'rover retrieve' command - check for remote data that we don't already have, download it and ingest it.
"""


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
        self._rover_cmd = args.rover_cmd
        self._mseed_cmd = args.mseed_cmd
        self._config = config
        # leap seconds not used here, but avoids multiple threads all downloading later
        check_leap(args.leap, args.leap_expire, args.leap_file, args.leap_url, self._log)
        clean_old_files(self._temp_dir, args.temp_expire * 60 * 60 * 24, match_prefixes(RETRIEVEFILE), self._log)

    def run(self, args, fetch):
        self._assert_single_use()
        # check these so we fail early
        check_cmd('%s -h' % self._rover_cmd, 'rover', 'rover', self._log)
        check_cmd('%s -h' % self._mseed_cmd, 'mseedindex', 'mseed-cmd', self._log)
        if not exists(self._temp_dir):
            makedirs(self._temp_dir)
        if len(args) == 0 or len(args) > 3:
            raise Exception('Usage: rover %s (file|sncl begin [end])' % RETRIEVE)
        else:
            # input is a temp file as we prepend parameters
            path = unique_path(self._temp_dir, RETRIEVEFILE, args[0])
            try:
                if len(args) == 1:
                    copyfile(args[0], path)
                else:
                    build_file(path, *args)
                self._query(path)
                if fetch:
                    return self._fetch()
                else:
                    return self._display()
            finally:
                unlink(path)

    def _query(self, up):
        """
        Populate teh download manager by comparing the data from the
        availability service with the local index.
        """
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

    def _fetch(self):
        """
        Fetch data from the download manager.
        """
        result = self._download_manager.download()
        if self._post_compact:
            self._log.info('Checking for duplicate data')
            Compacter(NewConfig(self._config, all=True, compact_list=True)).run([])
        return result

    def _display(self):
        """
        Display data from the download manager.
        """
        return self._download_manager.display()

    def _prepend_options(self, up):
        tmp = unique_path(self._temp_dir, RETRIEVEFILE, up)
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
        down = unique_path(self._temp_dir, RETRIEVEFILE, up)
        return post_to_file(self._availability_url, up, down, self._log)

    def _sort_availability(self, down):
        tmp = unique_path(self._temp_dir, RETRIEVEFILE, down)
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
    Implement the retrieve command.
    """
    return Retriever(config).run(config.args.args, fetch)
