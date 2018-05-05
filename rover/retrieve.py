
from datetime import datetime
from os import unlink, makedirs
from os.path import join
from re import match
from shutil import copyfile

from .download import DownloadManager
from .config import RETRIEVE
from .coverage import Coverage, Sncl
from .sqlite import SqliteSupport
from .utils import uniqueish, canonify, post_to_file, unique_filename, run, parse_time, check_cmd

RETRIEVEFILE = 'rover_retrieve'
EARLY = datetime(1900, 1, 1)


class Retriever(SqliteSupport):
    """
    Call the availability service, compare with the index, and
    then call the DownloadManager to retrieve the missing data
    (which are ingested and indexed by the Downloader).
    """

    def __init__(self, db, temp_dir, availability, tolerance, n_workers, dataselect, rover, mseedindex,
                 verbosity, dev, log_unique, args, log):
        super().__init__(db, log)
        self._download_manager = DownloadManager(n_workers, dataselect, rover, mseedindex, temp_dir, verbosity, dev,
                                                 log_unique, args, log)
        self._temp_dir = canonify(temp_dir)
        self._availability = availability
        self._tolerance = tolerance

    def retrieve(self, up):
        """
        Retrieve the data specified in the given file (format as for
        availability service).
        """
        self._prepend_options(up)
        down = self._post_availability(up)
        try:
            self._sort_availability(down)
            for remote in self._parse_availability(down):
                self._log.debug('Available data: %s' % remote)
                local = self._scan_index(remote.sncl)
                self._log.debug('Local data: %s' % local)
                self._request_download(remote.subtract(local))
            self._download_manager.run()
        finally:
            unlink(down)

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
        return post_to_file(self._availability, up, down, self._log)

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
        return Sncl(n, s, l, c), parse_time(b), parse_time(e)

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
                        availability = Coverage(self._tolerance, sncl)
                    availability.add_timespan(b, e)
            if availability:
                yield availability

    def _scan_index(self, sncl):
        # todo - we could maybe use time range from initial query?  or from availability?
        availability = Coverage(self._tolerance, sncl)
        def callback(row):
            b, e = row
            b, e = parse_time(b), parse_time(e)
            availability.add_timespan(b, e)
        self._foreachrow('''select starttime, endtime 
                                from tsindex 
                                where network=? and station=? and location=? and channel=?
                                order by starttime, endtime''',
                         (sncl.net, sncl.sta, sncl.loc, sncl.cha),
                         callback)
        return availability

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


def retrieve(core):
    """
    Implement the retrieve command - download data that is available and
    that we don't already have.
    """
    # check these two comands so we fail early
    check_cmd('%s -h' % core.args.rover_cmd, 'rover', 'rover', core.log)
    check_cmd('%s -h' % core.args.mseed_cmd, 'mseedindex', 'mseed-cmd', core.log)
    temp_dir = canonify(core.args.temp_dir)
    makedirs(temp_dir, exist_ok=True)
    retriever = Retriever(core.db, temp_dir, core.args.availability_url, core.args.timespan_tol,
                          core.args.download_workers, core.args.dataselect_url, core.args.rover_cmd,
                          core.args.mseed_cmd, core.args.verbosity, core.args.dev, core.args.log_unique,
                          core.args, core.log)
    if len(core.args.args) == 0 or len(core.args.args) > 3:
        raise Exception('Usage: rover %s (file|sncl begin [end])' % RETRIEVE)
    else:
        # guarantee always called with temp file because we prepend options
        path = temp_path(temp_dir, core.args.args[0])
        try:
            if len(core.args.args) == 1:
                copyfile(core.args.args[0], path)
            else:
                build_file(path, *core.args.args)
            retriever.retrieve(path)
        finally:
            unlink(path)
