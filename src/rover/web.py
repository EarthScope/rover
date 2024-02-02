
import os
from sqlite3 import OperationalError
from threading import Thread
from time import sleep
from http.server import BaseHTTPRequestHandler, HTTPServer

from .manager import INCONSISTENT, UNCERTAIN
from .args import HTTPBINDADDRESS, HTTPPORT, RETRIEVE, DAEMON, WEB
from .download import DEFAULT_NAME
from .process import ProcessManager
from .sqlite import SqliteSupport, NoResult
from .utils import process_exists, format_time_epoch, format_time_epoch_local, safe_unlink

"""
The 'rover web' command - run a web service that displays information on the download manager.
"""


class DeadMan(Thread):
    """
    Repeatedly check the parent process and exit when that dies.

    (Maybe processes should do this anyway with HUP, but this seems to be needed...)
    """

    def __init__(self, log, ppid, server, log_path):
        super().__init__()
        self._log = log
        self._ppid = ppid
        self._server = server
        self._log_path = log_path
        self._log.debug('DeadMan watching PID %d' % self._ppid)

    def run(self):
        while self._ppid != 1 and process_exists(self._ppid):
            sleep(1)
        self._log.info('Exiting because parent exited')
        if self._log_path and os.path.exists(self._log_path) and os.path.getsize(self._log_path) == 0:
                    safe_unlink(self._log_path)
        self._server.shutdown()
        sleep(1)
        exit()


class RequestHandler(BaseHTTPRequestHandler):
    """
    Generate the web page.

    BaseHTTPRequestHandler is part of the standard Python library HTTP server code - we extend it for this
    particular application.
    """

    def do_GET(self):
        """
        This method is called when the server receives a GET request.

        We detect what is running and generate the appropriate response.
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self._html_header()
        self._write('<h1>ROVER</h1>')
        pid, command = self.server.process_manager.current_command()
        if command == DAEMON:
            self._do_daemon()
        elif command == RETRIEVE:
            self._do_retrieve()
        else:
            self._do_quiet()
        self._html_footer()

    def _write(self, text):
        self.wfile.write(text.encode('ascii'))

    def _html_header(self):
        self._write('''<html lang="en">
  <head>
    <meta charset="ascii">
    <title>ROVER</title>
    <style>
* {
  font-family: monospace;
}
    </style>
  </head>
  <body>
''')

    def _html_footer(self):
        self._write('''
  </body>
</html>
''')

    def _do_quiet(self):
        self._write('<p>No daemon or retrieve process is running.</p>')

    def _do_daemon(self):
        self._write('<h2>Subscription Status</h2>')
        count = [0]

        def callback(row):
            count[0] += 1
            (id, file, availability_url, dataselect_url, creation_epoch, last_check_epoch,
             last_error_count, consistent) = row
            self._write('<h3>Subscription %d</h3>' % id)
            self._write('''<p><pre>File: <a href="file://%s">%s</a>
Availability URL: <a href="%s">%s</a>
Dataselect URL: <a href="%s">%s</a>
Created: %s (%s local)
Last active: %s (%s local)</pre></p>''' %
                        (file, file, availability_url, availability_url, dataselect_url, dataselect_url,
                         format_time_epoch(creation_epoch), format_time_epoch_local(creation_epoch),
                         format_time_epoch(last_check_epoch) if last_check_epoch else 'never',
                         format_time_epoch_local(last_check_epoch) if last_check_epoch else 'never'
                        ))
            self._write_progress(id, last_check_epoch, last_error_count, consistent)

        try:
            self.server.foreachrow('''SELECT id, file, availability_url, dataselect_url, creation_epoch,
                                             last_check_epoch, last_error_count, consistent
                                        FROM rover_subscriptions ORDER BY id''', tuple(), callback)
        except OperationalError:
            pass
        if not count[0]:
            self._write('<p>No subscriptions</p>')
        self._write_explanation()

    def _do_retrieve(self):
        self._write('<h2>Retrieval Progress</h2>')
        self._write_progress(DEFAULT_NAME, None, None, None)
        self._write_explanation()

    def _write_progress(self, name, last_check_epoch, last_error_count, consistent):
        try:
            initial_stations, remaining_stations, initial_time, remaining_time, n_retries, download_retries = \
                self.server.fetchone('''SELECT initial_stations, remaining_stations, initial_time, remaining_time,
                                               n_retries, download_retries
                                          FROM rover_download_stats WHERE submission = ?''', (name,))
            self._write('<p>Progress for download attempt %d of %d:<pre>\n' % (n_retries, download_retries))
            self._write_bar('stations', initial_stations, remaining_stations)
            self._write_bar('timespan', initial_time, remaining_time)
            self._write('</pre></p>')
        except NoResult:
            if last_error_count:
                self._write('<p>Inactive.  WARNING: Last download had errors, so data may be incomplete.</p>')
            elif last_check_epoch:
                if consistent == INCONSISTENT:
                    self._write('''<p>Inactive.  WARNING: last download detected inconsistent web services
                                   (eg dataselect not providing data promised by availability)''')
                elif consistent == UNCERTAIN:
                    self._write('''<p>Inactive.  Last download had no errors but could not check web service consistency
                                   (unlikely to be a problem).''')
                else:
                    self._write('<p>Inactive.  Latest download had no errors.</p>')
            else:
                self._write('<p>Inactive.  Waiting for initial download.</p>')
        except OperationalError:
            self._write('<p>Error: no statistics in database.</p>')

    def _write_bar(self, label, initial, current):
        # there's some massaging of numbers here because the seconds might not match exactly
        # due to fractions of a sample being added to include boundary values
        percent = max(0, min(100, int(100 * (initial - current) / max(1, initial))))
        n = int(percent / 2 + 0.5)
        self._write('%10s: %10d/%-10d  (%3d%%)  |%s|\n' %
                    (label, initial - current, initial, percent, '#' * n + ' ' * (50-n)))

    def _write_explanation(self):
        self._write('''
<h2>Notes</h2>
<ul>
<li>Progress values are based on data still to be downloaded; they do not include data within the pipeline.</li>
<li>The stations statistic is the number of distinct Net_Sta that will be requested.</li>
<li>The timespan statistic is the total time (s) covered by the data in the downloads.</li>
<li>Firefox will not open file:// URLs, but you can copy them to the address bar, where they will work.</li>
</ul>
''')

    def log_message(self, format, *args):
        pass


class Server(HTTPServer, SqliteSupport):
    """
    Extend the standard HTTP server to include a database connection and access to process data.
    """

    def __init__(self, config, address, handler):
        HTTPServer.__init__(self, address, handler)
        SqliteSupport.__init__(self, config)
        self.process_manager = ProcessManager(config)


class ServerStarter:
    """
### Web

    rover web

    rover web --http-bind-address 0.0.0.0 --http-port 8080

    rover retrieve --web ...   # the default

Starts a web server that provides information on the progress of the download
manager. ROVER's default configuration starts `rover web` automatically.
The flag`--no-web` prevents ROVER's web server from launching in accordance
with `rover retrieve`.

##### Significant Options

@web
@http-bind-address
@http-port
@verbosity
@log-dir
@log-verbosity

##### Examples

    rover retrieve --no-web

will run retrieve without the web server.

    """

    def __init__(self, config):
        self._bind_address = config.arg(HTTPBINDADDRESS)
        self._http_port = config.arg(HTTPPORT)
        self._ppid = ProcessManager(config).current_command()[0]
        if not self._ppid:
            raise Exception('Cannot start web server independently of retrieve')
        self._log = config.log
        self._log_path = config.log_path
        self._config = config

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % WEB)
        server = Server(self._config, (self._bind_address, self._http_port), RequestHandler)
        DeadMan(self._log, self._ppid, server, self._log_path).start()
        self._log.info('Starting HTTP server on http://%s:%d' % (self._bind_address, self._http_port))
        server.serve_forever()
