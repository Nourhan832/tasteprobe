"""Dependency-free HTTP entrypoint. Run python server.py; keys stay server-side."""
import argparse
import json
import os
import time
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from service import Service

ROOT = Path(__file__).resolve().parent / "dist"
STATIC = {"/": ("index.html", "text/html; charset=utf-8"), "/index.html": ("index.html", "text/html; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8")}


class Server(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, service=None):
        super().__init__(address, Handler)
        self.service = service or Service()
        self.requests = {}
        self.rate_lock = threading.Lock()
        self.stop_pruning = threading.Event()
        self.pruner = threading.Thread(target=self._prune_sessions, daemon=True)
        self.pruner.start()

    def _prune_sessions(self):
        while not self.stop_pruning.wait(30):
            with self.service.lock:
                self.service.prune()

    def server_close(self):
        self.stop_pruning.set()
        super().server_close()


class Handler(BaseHTTPRequestHandler):
    server_version = "TasteProbe"

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *args):
        pass  # Do not log searches or session capability tokens.

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
        super().end_headers()

    def respond(self, status, data):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/config":
            return self.respond(200, {"live_available": bool(os.environ.get("QLOO_API_KEY")) or os.environ.get("QLOO_ENABLED") == "1", "demo_available": True,
                                      "session_retention_minutes": 60})
        if path == "/health":
            return self.respond(200, {"status": "ok"})
        if path not in STATIC:
            return self.respond(404, {"error": "Not found"})
        name, mime = STATIC[path]
        raw = (ROOT / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        # Same-origin JSON endpoints. No CORS and no form-encoded mutations.
        origin = self.headers.get("Origin")
        expected = os.environ.get("APP_ORIGIN") or "http://" + self.headers.get("Host", "")
        if origin and origin != expected:
            return self.respond(403, {"error": "Cross-origin requests are not allowed"})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.respond(415, {"error": "Use application/json"})
        if self.headers.get("Transfer-Encoding"):
            return self.respond(400, {"error": "Transfer encoding unsupported"})
        now = time.monotonic()
        with self.server.rate_lock:
            self.server.requests = {k: v for k, v in self.server.requests.items() if v and now-v[-1] < 60}
            queue = self.server.requests.setdefault(self.client_address[0], deque())
            while queue and now-queue[0] >= 60:
                queue.popleft()
            if len(queue) >= 60:
                return self.respond(429, {"error": "Please wait a minute before trying again"})
            queue.append(now)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 8192:
                return self.respond(413, {"error": "Request body must be 1 to 8192 bytes"})
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError("Expected a JSON object")
            service = self.server.service
            if self.path == "/api/search":
                query, kind = body.get("query"), body.get("kind")
                if not isinstance(query, str) or not 1 <= len(query.strip()) <= 200 or kind not in ("movie", "artist", "book"):
                    raise ValueError("Enter a short search and a supported category")
                data = service.search(query, kind)
            elif self.path == "/api/session":
                study = body.get("study", False)
                if not isinstance(study, bool):
                    raise ValueError("Study must be true or false")
                data = service.create(body.get("mode", "demo"), body.get("seeds"), study)
            elif self.path == "/api/answer":
                data = service.answer(body.get("session_id"), body.get("entity_id"), body.get("answer"))
            elif self.path == "/api/state":
                data = service.state(body.get("session_id"))
            elif self.path == "/api/delete":
                service.delete(body.get("session_id"))
                data = {"deleted": True}
            elif self.path == "/api/undo":
                data = service.undo(body.get("session_id"))
            else:
                return self.respond(404, {"error": "Not found"})
            self.respond(200, data)
        except HTTPError as exc:
            self.respond(502, {"error": f"Qloo returned HTTP {exc.code}. Check assigned access and quota; no demo fallback was used."})
        except (URLError, TimeoutError):
            self.respond(502, {"error": "Qloo could not be reached. Please retry; no demo fallback was used."})
        except LookupError:
            self.respond(410, {"error": "Session expired; start again"})
        except (ValueError, TypeError) as exc:
            self.respond(400, {"error": str(exc)[:220]})
        except RuntimeError as exc:
            self.respond(503, {"error": str(exc)[:220]})
        except Exception:
            self.respond(500, {"error": "Unexpected server error. Restart the session or check the server configuration."})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8766")))
    args = parser.parse_args()
    server = Server((args.host, args.port))
    print(f"TasteProbe serving at http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
