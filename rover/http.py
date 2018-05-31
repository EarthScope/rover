
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import getppid
from sqlite3 import OperationalError
from threading import Thread
from time import sleep

from .process import ProcessManager
from .args import BINDADDRESS, HTTPPORT, RETRIEVE, DAEMON, WEB
from .utils import process_exists
from .sqlite import SqliteSupport


class DeadMan(Thread):

    def __init__(self, log, ppid, server):
        super().__init__()
        self._log = log
        self._ppid = ppid
        self._server = server
        self._log.debug('DeadMan watching PID %d' % self._ppid)

    def run(self):
        while self._ppid != 1 and process_exists(self._ppid):
            sleep(1)
        self._log.info('Exiting because parent exited')
        self._server.shutdown()
        sleep(1)
        exit()


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self._html_header()
        self._write('<h1>Rover</h1>')
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
    <title>Rover</title>
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

    def _do_retrieve(self):
        self._write('<h2>Retrieval Progress</h2>')
        try:
            initial_coverages, remaining_coverages, initial_time, remaining_time = \
                self.server.fetchone('''select initial_coverages, remaining_coverages, initial_time, remaining_time
                                          from rover_download_stats''')
            self._write_progress(initial_coverages, remaining_coverages, initial_time, remaining_time)
        except OperationalError:
            self._write('<p>Error: no statistics in database</p>')
        self._write_explanation()

    def _write_progress(self, initial_coverages, remaining_coverages, initial_time, remaining_time):
        self._write('<p><pre>\n')
        self._write_bar('SNCLs', initial_coverages, remaining_coverages)
        self._write_bar('timespan', initial_time, remaining_time)
        self._write('</pre></p>')

    def _write_bar(self, label, initial, current):
        percent = int(100 * (initial - current) / initial)
        n = int(percent / 2 + 0.5)
        self._write('%10s: %10d/%-10d  (%3d%%)  |%s|\n' %
                    (label, initial - current, initial, percent, '#' * n + ' ' * (50-n)))

    def _write_explanation(self):
        self._write('''
<h2>Notes</h2>
<ul>
<li>Progress values are based on data still to be downloaded; they do not include data within the pipeline.</li>
<li>The SNCL statistics is the number of distinct SNCLs that will be requested.</li>
<li>The timespan statistics is the total time (s) covered by the data in the downloads.</li>
</ul>
''')


class Server(HTTPServer, SqliteSupport):

    def __init__(self, config, address, handler):
        HTTPServer.__init__(self, address, handler)
        SqliteSupport.__init__(self, config)
        self.process_manager = ProcessManager(config)


class ServerStarter:

    def __init__(self, config):
        self._bind_address = config.arg(BINDADDRESS)
        self._http_port = config.arg(HTTPPORT)
        self._ppid = getppid()
        self._log = config.log
        self._config = config

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % WEB)
        server = Server(self._config, (self._bind_address, self._http_port), RequestHandler)
        DeadMan(self._log, self._ppid, server).start()
        self._log.info('Starting HTTP server on http://%s:%d' % (self._bind_address, self._http_port))
        server.serve_forever()
