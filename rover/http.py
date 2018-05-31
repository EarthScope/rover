
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import getppid
from threading import Thread
from time import sleep

from .args import BINDADDRESS, HTTPPORT
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
        self.wfile.write('hello mother'.encode('ascii'))


class Server(HTTPServer):

    def __init__(self, config, address, handler):
        self._log = config.log
        self._db = config.db
        super().__init__(address, handler)


class ServerStarter(SqliteSupport):

    def __init__(self, config):
        super().__init__(config)
        self._bind_address = config.arg(BINDADDRESS)
        self._http_port = config.arg(HTTPPORT)
        self._ppid = getppid()
        self._log = config.log
        self._config = config

    def run(self, args):
        # todo check args
        server = Server(self._config, (self._bind_address, self._http_port), RequestHandler)
        DeadMan(self._log, self._ppid, server).start()
        self._log.info('Starting HTTP server on %s:%d' % (self._bind_address, self._http_port))
        server.serve_forever()
