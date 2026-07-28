#!/usr/bin/env python3
"""MicroFlask API — lightweight HTTP item catalog service.

Runs a WSGI application via http.server.
Invoked by systemd or directly via start.sh.
"""

import os
import sys
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from handlers import handle_request, handle_health

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8080"))

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="var/log/app.log",
)
log = logging.getLogger("microflask")


class MicroFlaskHandler(BaseHTTPRequestHandler):
    """HTTP request handler wrapping WSGI-style handlers."""

    def do_GET(self):
        environ = self._build_environ()
        status, data = handle_request(environ)
        self._respond(status, data)

    def do_POST(self):
        environ = self._build_environ()
        content_length = int(self.headers.get("Content-Length", 0))
        environ["wsgi.input"] = self.rfile.read(content_length)
        status, data = handle_request(environ)
        self._respond(status, data)

    def _build_environ(self):
        return {
            "REQUEST_METHOD": self.command,
            "PATH_INFO": self.path,
            "QUERY_STRING": self.path.split("?", 1)[1] if "?" in self.path else "",
            "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            "SERVER_NAME": HOST,
            "SERVER_PORT": str(PORT),
        }

    def _respond(self, status_code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        log.info("request: %s", fmt % args)


def write_state(status):
    os.makedirs("state", exist_ok=True)
    with open("state/app_status", "w") as f:
        f.write(status + "\n")


def main():
    write_state("starting")
    log.info("starting on %s:%s", HOST, PORT)
    server = HTTPServer((HOST, PORT), MicroFlaskHandler)
    write_state("healthy")
    log.info("listening on port %s", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        write_state("stopped")
        log.info("shutdown complete")
    except Exception as exc:
        write_state("failed")
        log.error("fatal: %s", exc)
        raise


if __name__ == "__main__":
    main()
