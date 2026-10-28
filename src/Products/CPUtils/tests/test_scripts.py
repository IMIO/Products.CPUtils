# -*- coding: utf-8 -*-
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from Products.CPUtils.scripts import utils

import base64
import threading
import unittest


class ZopeLikeHandler(BaseHTTPRequestHandler):
    """Asks for Basic auth, returns 404 on /missing and echoes POST data."""

    def _reply(self, body=""):
        auth = "Basic " + base64.b64encode(b"admin:secret").decode()
        if self.headers.get("Authorization") != auth:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="Zope"')
            self.end_headers()
            return
        self.send_response(self.path == "/missing" and 404 or 200)
        self.end_headers()
        self.wfile.write(("%s Stéphan %s" % (self.path, body)).encode("utf8"))

    def do_GET(self):
        self._reply()

    def do_POST(self):
        self._reply(self.rfile.read(int(self.headers["Content-Length"])).decode())

    def log_message(self, *args):
        pass


class TestUrlread(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("localhost", 0), ZopeLikeHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = "http://localhost:%s" % self.server.server_port
        utils.user, utils.pwd = "admin", "secret"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_urlread(self):
        self.assertEqual(utils.urlread(self.url + "/ok"), "/ok Stéphan ")
        # an HTTP error page is returned, not raised (scripts test its text)
        self.assertEqual(utils.urlread(self.url + "/missing"), "/missing Stéphan ")
        self.assertEqual(utils.urlread(self.url + "/post", {"a0": "on"}), "/post Stéphan a0=on")
        utils.pwd = "wrong"
        self.assertEqual(utils.urlread(self.url + "/ok"), "")
