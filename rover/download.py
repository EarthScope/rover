import os

from .args import DOWNLOAD, TEMPDIR, DELETEFILES, INGEST, \
    TEMPEXPIRE, HTTPTIMEOUT, \
    HTTPRETRIES, DATASELECTURL
from .ingest import Ingester
from .sqlite import SqliteSupport
from .utils import uniqueish, get_to_file, unique_filename, \
    clean_old_files, match_prefixes, create_parents, unique_path, \
    safe_unlink, file_size, post_to_file, diagnose_error

"""
The 'rover download' command - download data from a URL (and then call ingest).
"""


TMPREQUEST = 'rover_availability_request'
TMPRESPONSE = 'rover_availability_response'
TMPDOWNLOAD = 'rover_download'

# name of source when not a subscription
DEFAULT_NAME = -1


class Downloader(SqliteSupport):
    """
### Download

    rover download url [path]

    rover download file [path]

If given a URL, download a single request (typically for a day) to the given path, ingest and index it.  If no path
is given then a temporary file is created and deleted after use.  Rover treats the argument as a URL if it contains
the characters "://".


The url should be for a Data Select service, and should not request data that spans multiple calendar days.

If given a file name, POST that file to URL given by the `dataselect-url` configuration parameter, download the
response to the given path,  ingest and index it.  If no path is given then a temporary file is created and deleted
after use.

This task is the main low-level task called in the processing pipeline (it calls ingest and index as needed).
Because of this, to reduce the quantity of unhelpful logs generated when a pipeline is running, empty logs are
automatically deleted on exit.

##### Significant Parameters

@dataselect-url
@temp-dir
@http-timeout
@http-retries
@delete-files
@ingest
@index
@verbosity
@log-dir
@log-verbosity

In addition, parameters for sub-commands (ingest, index) will be used - see help for those
commands for more details.

##### Examples

    rover download \\
    'http://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2010-02-27T06:30:00.000&end=2010-02-27T10:30:00.000'

will download, ingest and index data from the given URL.

    rover download myrequest.txt

will download, ingest and index data from `dataselect-url` after POSTing `myrequest.txt`.

"""

# The only complex thing here is that these may run in parallel.  That means that
# multiple ingest instances can be running in parallel, all using mseedindex.
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
        self._temp_dir = config.dir(TEMPDIR)
        self._dataselect_url = config.arg(DATASELECTURL)
        self._delete_files = config.arg(DELETEFILES)
        self._blocksize = 1024 * 1024
        self._ingest = config.arg(INGEST)
        self._http_timeout = config.arg(HTTPTIMEOUT)
        self._http_retries = config.arg(HTTPRETRIES)
        self._config = config
        clean_old_files(self._temp_dir, config.arg(TEMPEXPIRE), match_prefixes(TMPDOWNLOAD), self._log)

    def run(self, args):
        """
        Download the give URL or file, then call ingest and index before deleting.
        """
        if len(args) < 1 or len(args) > 2:
            raise Exception('Usage: rover %s url [path]' % DOWNLOAD)
        in_path_or_url = args[0]
        db_path = self._ingesters_db_path(in_path_or_url)
        if '://' in in_path_or_url:
            url, in_path, get = in_path_or_url, None, True
            if '&' not in url:
                self._log.warn(('The URL provided is "%s" - this does not contain any ampersands.  ' +
                                'You may have forgotten to quote the URL (and should expect failure).') % url)
        else:
            url, in_path, get = self._dataselect_url, in_path_or_url, False
            if not os.path.exists(in_path):
                raise Exception('Could not find file "%s"' % in_path)
        if len(args) == 2:
            out_path, delete_out = args[2], False
        else:
            out_path, delete_out = unique_path(self._temp_dir, TMPDOWNLOAD, in_path_or_url), True
        try:
            if self._do_download(get, url, in_path, out_path):  # False when no data available
                if self._ingest:
                    Ingester(self._config).run([out_path], db_path=db_path)
        finally:
            if self._delete_files:
                if delete_out:
                    safe_unlink(out_path)
                log_path = self._config.log_path
                # avoid lots of empty logs cluttering things up
                if os.path.exists(log_path) and file_size(log_path) == 0:
                    safe_unlink(log_path)
                safe_unlink(db_path)

    def _do_download(self, get, url, in_path, out_path):
        # previously we extracted the file name from the header, but the code
        # failed in python 2 (looked like a backport library bug), so now we let the user specify,
        if os.path.exists(out_path):
            raise Exception('Path %s for download already exists' % out_path)
        create_parents(out_path)

        if get:
            response, check_status = get_to_file(url, out_path,
                                                 self._http_timeout, self._http_retries, self._log)
            check_status()
        else:
            try:
                response, check_status = post_to_file(url, in_path, out_path,
                                                      self._http_timeout, self._http_retries, self._log)
                check_status()
            except Exception as e:
                diagnose_error(self._log, str(e), in_path, out_path, copied=False)
                raise

        # write download byte count to stdout as feedback to caller
        if response:
            print ('{"download_byte_count":%d}' % os.path.getsize(response))

        return response

    def _ingesters_db_path(self, url):
        name = uniqueish('rover_ingester', url)
        return unique_filename(os.path.join(self._temp_dir, name))
