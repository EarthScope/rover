
import os
from threading import Thread
from time import sleep
from http.server import BaseHTTPRequestHandler, HTTPServer

from .args import HTTPBINDADDRESS, HTTPPORT, WEB
from .utils import process_exists, safe_unlink

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
        # Daemon/subscription status removed; show simple message.
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

    def log_message(self, format, *args):
        pass


class Server(HTTPServer):
    """Lightweight HTTP server for the rover status page."""

    def __init__(self, address, handler):
        super().__init__(address, handler)


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
        self._ppid = os.getppid()
        self._log = config.log
        self._log_path = config.log_path

    def run(self, args):
        if args:
            raise Exception('Usage: rover %s' % WEB)
        server = Server((self._bind_address, self._http_port), RequestHandler)
        DeadMan(self._log, self._ppid, server, self._log_path).start()
        self._log.info('Starting HTTP server on http://%s:%d' % (self._bind_address, self._http_port))
        server.serve_forever()
