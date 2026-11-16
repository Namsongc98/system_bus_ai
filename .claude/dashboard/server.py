#!/usr/bin/env python3
"""Local read-only web server for the harness dashboard.

Usage: python3 .claude/dashboard/server.py [--port 4317]
There is deliberately no --host option: it only ever listens on loopback.
"""
from __future__ import annotations

import argparse
import errno
import json
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import collect  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
                               "base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Cross-Origin-Resource-Policy": "same-origin",
}
SNAPSHOT_TTL = 2.0


class SnapshotCache:
    def __init__(self, build: Callable[[], dict], ttl: float = SNAPSHOT_TTL) -> None:
        self.build = build
        self.ttl = ttl
        self.lock = threading.Lock()
        self.expires = 0.0
        self.body = b""

    def get(self) -> bytes:
        with self.lock:
            if time.monotonic() >= self.expires:
                self.body = json.dumps(self.build(), ensure_ascii=False).encode("utf-8")
                self.expires = time.monotonic() + self.ttl
            return self.body


class Handler(BaseHTTPRequestHandler):
    server_version = "harness-dashboard"
    sys_version = ""
    cache: SnapshotCache

    def host_allowed(self) -> bool:
        port = self.server.server_address[1]
        return self.headers.get("Host", "") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def send_body(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_json_error(self, status: int, code: str) -> None:
        self.send_body(status, "application/json; charset=utf-8", json.dumps({"error": code}).encode())

    def do_GET(self) -> None:
        if not self.host_allowed():
            self.send_json_error(403, "host_not_allowed")
            return
        path = self.path.split("?", 1)[0]
        try:
            if path == "/api/snapshot" and self.headers.get("Sec-Fetch-Site", "none") not in {"none", "same-origin"}:
                self.send_json_error(403, "cross_site")
            elif path == "/api/snapshot":
                self.send_body(200, "application/json; charset=utf-8", self.cache.get())
            elif path in STATIC_FILES:
                name, content_type = STATIC_FILES[path]
                self.send_body(200, content_type, (STATIC_DIR / name).read_bytes())
            else:
                self.send_json_error(404, "not_found")
        except collect.DetectorUnavailable:
            self.send_json_error(503, "secret_scanner_unavailable")
        except BrokenPipeError:
            pass
        except Exception:
            traceback.print_exc()
            self.send_json_error(500, "internal_error")

    def do_HEAD(self) -> None:
        self.do_GET()

    def reject_method(self) -> None:
        self.send_json_error(405, "read_only")

    do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_TRACE = do_CONNECT = reject_method

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        self.send_json_error(code, "bad_request")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def create_server(port: int, build: Callable[[], dict]) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"cache": SnapshotCache(build)})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    server.daemon_threads = True
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Harness dashboard (local, read-only)")
    parser.add_argument("--port", type=int, default=4317)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    try:
        detector = collect.load_detector(root)
    except collect.DetectorUnavailable:
        print("Không nạp được bộ quét secret trong .claude/hooks/claude_hook.py nên dashboard không chạy.", file=sys.stderr)
        return 1
    try:
        server = create_server(args.port, lambda: collect.build_snapshot(root, detector=detector))
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            print(f"Cổng {args.port} đang được dùng. Chạy lại với --port <số khác>.", file=sys.stderr)
            return 1
        raise
    print(f"Harness dashboard: http://127.0.0.1:{server.server_address[1]}  (Ctrl+C để dừng)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
