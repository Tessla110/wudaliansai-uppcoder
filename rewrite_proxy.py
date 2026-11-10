"""Uppcoder /app/ front-door for wudaliansai.

Uppcoder serves the app under <public-host>/app/ and forwards to
127.0.0.1:8000. The wudaliansai binary builds absolute play URLs from
the request Host header, using its built-in default port (18765) and no
/app/ prefix, so those links would be dead behind Uppcoder's proxy.
This tiny proxy listens on 8000, forwards everything to the app on
127.0.0.1:18765, and rewrites the /live.m3u body so play links become
https://<public-host>/app/play/<key>. /play/<key> itself is a 302 to a
CDN, so it passes through untouched.
"""
import http.client
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM_HOST = "127.0.0.1"
UPSTREAM_PORT = 18765
LISTEN_PORT = 8000
HOP = {"connection", "keep-alive", "proxy-connection", "te",
       "trailer", "proxy-authorization", "proxy-authenticate",
       "transfer-encoding", "upgrade"}
PLAY_RE = re.compile(rb"https?://[^/\s\"']+/play/")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _handle(self):
        host = self.headers.get("Host", "localhost")
        body = None
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            body = self.rfile.read(length)
        conn = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=60)
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
        try:
            conn.request(self.command, self.path, body=body, headers=headers)
            resp = conn.getresponse()
            data = resp.read()
        finally:
            conn.close()
        if self.path.split("?")[0] == "/live.m3u" and resp.status == 200:
            data = PLAY_RE.sub(b"https://" + host.encode() + b"/app/play/", data)
        self.send_response(resp.status, resp.reason)
        sent_len = False
        for k, v in resp.getheaders():
            if k.lower() in HOP:
                continue
            if k.lower() == "content-length":
                v = str(len(data))
                sent_len = True
            self.send_header(k, v)
        if not sent_len:
            self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    do_GET = _handle
    do_HEAD = _handle
    do_POST = _handle

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), Handler).serve_forever()
