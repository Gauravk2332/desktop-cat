"""
core/api.py — Async HTTP API that external tools use to interact with the cat.

Runs in a daemon thread so it doesn't block the GUI.
"""

import json
from queue import Queue
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

import config

# Global action queue consumed by the engine every tick
action_queue: Queue = Queue()

# Global state reference set from main.py
_STATE = None


def set_state_ref(state) -> None:
    global _STATE
    _STATE = state


class _APIHandler(BaseHTTPRequestHandler):
    """Minimal JSON-over-HTTP handler."""

    def log_message(self, fmt, *args):
        pass   # suppress HTTP log noise

    def _send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            try:
                s = _STATE
                cats_data = []
                for cat in s.cats:
                    cats_data.append({
                        "id": cat["id"],
                        "state": cat["state"],
                        "energy": round(cat.get("energy", 0.0), 1),
                        "hunger": round(cat.get("hunger", 0.0), 1),
                        "boredom": round(cat.get("boredom", 0.0), 1),
                        "facing": cat.get("facing", True),
                        "x": round(cat.get("x", 0.0), 0),
                        "y": round(cat.get("y", 0.0), 0),
                        "at_home": cat.get("at_home", False),
                        "coat": cat.get("coat", 0),
                    })
                data = {
                    "status": "alive",
                    "state": "desktop-cat-v2-modular",
                    "cat_count": len(cats_data),
                    "cats": cats_data,
                    # Backward compat: first cat
                    "cat": cats_data[0] if cats_data else None,
                }
            except Exception:
                data = {"status": "alive", "state": "desktop-cat-v2-modular"}
            self._send_json(data)
        else:
            self._send_json({"error": "not_found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self._send_json({"error": "not_found"}, 404)
            return
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self._send_json({"error": "empty_body"}, 400)
            return
        try:
            data = json.loads(self.rfile.read(length))
        except Exception:
            self._send_json({"error": "invalid_json"}, 400)
            return

        action = data.get("action", "")
        if action not in ("pet", "feed", "wake"):
            self._send_json({"error": f"unknown_action: {action}"}, 400)
            return

        action_queue.put(action)
        self._send_json({"status": "ok", "action": action})


def start_api():
    """Start the HTTP server daemon on the configured port."""
    server = HTTPServer(("127.0.0.1", config.API_PORT), _APIHandler)
    t = Thread(target=server.serve_forever, daemon=True, name="cat-api")
    t.start()
