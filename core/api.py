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
_ENGINE = None


def set_state_ref(state) -> None:
    global _STATE
    _STATE = state


def set_engine_ref(engine) -> None:
    global _ENGINE
    _ENGINE = engine


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
        if parsed.path == "/test-sound":
            play_name = ""
            try:
                s = parsed.query.split("&") if parsed.query else []
                for item in s:
                    k, _, v = item.partition("=")
                    if k == "name":
                        play_name = v
            except Exception:
                pass
            if not play_name:
                play_name = "meow_short"
            engine = _ENGINE
            if engine:
                try:
                    engine.sound.play(play_name)
                    self._send_json({"status": "ok", "played": play_name})
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            else:
                self._send_json({"error": "engine not available"}, 503)
            return

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
        if action == "add_cat":
            s = _STATE
            if s:
                cat_id = s.add_cat()
                if cat_id is not None:
                    self._send_json({"status": "ok", "cat_id": cat_id})
                else:
                    self._send_json({"error": "max cats reached"}, 400)
            else:
                self._send_json({"error": "state not available"}, 503)
            return
        elif action == "remove_cat":
            s = _STATE
            if s:
                if len(s.cats) <= 1:
                    self._send_json({"error": "minimum 1 cat"}, 400)
                else:
                    s.cats.pop()
                    self._send_json({"status": "ok"})
            else:
                self._send_json({"error": "state not available"}, 503)
            return
        elif action == "set_coat":
            s = _STATE
            if s and s.cats:
                cat_id = int(data.get("cat_id", 0))
                coat = int(data.get("coat", 0))
                for cat in s.cats:
                    if cat["id"] == cat_id:
                        cat["coat"] = coat
                        break
                self._send_json({"status": "ok"})
            else:
                self._send_json({"error": "state not available"}, 503)
            return
        elif action == "agent_action":
            action_type = data.get("action_type", "SIT")
            params = data.get("params", {})
            agent_response = data.get("response", "")
            engine = _ENGINE
            if engine and hasattr(engine, '_execute_agent_action'):
                cat = _STATE.cats[0] if _STATE and _STATE.cats else None
                if cat:
                    engine._execute_agent_action(cat, action_type, params, 0.016)
                    self._send_json({"status": "ok", "action_type": action_type})
                else:
                    self._send_json({"error": "no cats"}, 400)
            else:
                self._send_json({"error": "engine not ready"}, 503)
            return
        elif action in ("pet", "feed", "wake"):
            action_queue.put(action)
            self._send_json({"status": "ok", "action": action})
            return
        else:
            self._send_json({"error": f"unknown_action: {action}"}, 400)


def start_api():
    """Start the HTTP server daemon on the configured port."""
    server = HTTPServer(("0.0.0.0", config.API_PORT), _APIHandler)
    t = Thread(target=server.serve_forever, daemon=True, name="cat-api")
    t.start()
