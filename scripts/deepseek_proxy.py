#!/usr/bin/env python3
"""Simple proxy: cat agent → clowbot → DeepSeek API.

Listens on port 18990, accepts OpenAI-compatible chat completions,
forwards to DeepSeek with our API key. No key exposed to gk-pc.
"""
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# Try reading from OpenClaw config
if not API_KEY:
    try:
        cfg = json.load(open("/root/.openclaw/openclaw.json"))
        providers = cfg.get("models", {}).get("providers", {})
        for p in providers.values():
            if "deepseek" in p.get("baseUrl", ""):
                API_KEY = p.get("apiKey", "")
                break
    except Exception:
        pass

# Fallback: try directly
if not API_KEY:
    try:
        import subprocess
        result = subprocess.run(
            ["openclaw", "config", "get", "models.providers.deepseek.apiKey"],
            capture_output=True, text=True, timeout=5
        )
        API_KEY = result.stdout.strip()
    except Exception:
        pass


PROXY_PATH = "/v1/chat/completions"


class ProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path != PROXY_PATH:
            self.send_response(404)
            self.end_headers()
            return
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)
        data = json.loads(body)

        # Ensure model is set
        data.setdefault("model", "deepseek-chat")
        data["stream"] = False

        req = Request(
            DEEPSEEK_URL,
            json.dumps(data).encode(),
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
        )
        try:
            resp = urlopen(req, timeout=15)
            result = json.loads(resp.read())
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        pass  # silent


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18990
    if not API_KEY:
        print("ERROR: no DeepSeek API key found", file=sys.stderr)
        sys.exit(1)
    server = HTTPServer(("0.0.0.0", port), ProxyHandler)
    print(f"DeepSeek proxy running on port {port}", file=sys.stderr)
    server.serve_forever()


if __name__ == "__main__":
    main()
