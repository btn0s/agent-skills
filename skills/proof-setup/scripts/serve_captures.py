#!/usr/bin/env python3
"""Serve the captures bucket on localhost with Range support (Safari needs it to play MP4).

Exposed to the tailnet by `tailscale serve --bg --set-path /captures http://127.0.0.1:8740`.
"""
import argparse, html, mimetypes, os, re, shutil, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PREFIX = "/captures"


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path = urllib.parse.urlsplit(path).path
        if path == PREFIX or path.startswith(PREFIX + "/"):  # tolerate an unstripped mount prefix
            path = path[len(PREFIX):] or "/"
        return super().translate_path(path)

    def list_directory(self, path):
        # Newest first; links stay relative so they work under any mount point.
        names = sorted((n for n in os.listdir(path) if not n.startswith(".")),
                       key=lambda n: os.path.getmtime(os.path.join(path, n)), reverse=True)
        rows = []
        for n in names:
            full = os.path.join(path, n)
            label = n + ("/" if os.path.isdir(full) else "")
            size = "" if os.path.isdir(full) else f"{os.path.getsize(full) / 1e6:.1f} MB"
            rows.append(f'<li><a href="{urllib.parse.quote(label)}">{html.escape(label)}</a> <small>{size}</small></li>')
        body = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
                "<title>captures</title><style>body{font:16px system-ui;margin:2rem;background:#101118;color:#eee}"
                "a{color:#ffb847}small{color:#889}</style><h1>captures</h1><ul>" + "".join(rows) + "</ul>").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.translate_path(self.path)
        rng = self.headers.get("Range")
        if not rng or not os.path.isfile(path):
            return super().do_GET()
        m = re.match(r"bytes=(\d*)-(\d*)$", rng.strip())
        size = os.path.getsize(path)
        if not m or (not m.group(1) and not m.group(2)):
            self.send_error(416)
            return
        if m.group(1):
            start, end = int(m.group(1)), int(m.group(2)) if m.group(2) else size - 1
        else:  # suffix range: last N bytes
            start, end = max(0, size - int(m.group(2))), size - 1
        end = min(end, size - 1)
        if start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return
        self.send_response(206)
        self.send_header("Content-Type", mimetypes.guess_type(path)[0] or "application/octet-stream")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = f.read(min(1 << 20, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.expanduser("~/dev/captures/public"))
    ap.add_argument("--port", type=int, default=8740)
    a = ap.parse_args()
    os.makedirs(a.dir, exist_ok=True)
    os.chdir(a.dir)
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()
