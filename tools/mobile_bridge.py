from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from core.paths import EVE_ROOT, ensure_project_dirs


BRIDGE_DIR = EVE_ROOT / "mobile_bridge"
INBOX = BRIDGE_DIR / "inbox.jsonl"
OUTBOX = BRIDGE_DIR / "outbox.jsonl"


def bridge_status() -> dict:
    ensure_project_dirs()
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    return {"bridge_dir": str(BRIDGE_DIR), "inbox": str(INBOX), "outbox": str(OUTBOX)}


def queue_mobile_message(message: str) -> Path:
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "message": message}
    with OUTBOX.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return OUTBOX


def read_outbox(limit: int = 20) -> list[dict]:
    if not OUTBOX.exists():
        return []
    rows = []
    for line in OUTBOX.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


class MobileBridgeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = json.dumps({"status": "ok", "bridge": bridge_status(), "outbox": read_outbox()}, ensure_ascii=False).encode("utf-8")
        elif parsed.path == "/send":
            query = parse_qs(parsed.query)
            msg = query.get("msg", [""])[0]
            path = queue_mobile_message(msg)
            body = json.dumps({"queued": str(path), "message": msg}, ensure_ascii=False).encode("utf-8")
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_mobile_bridge_server(host: str = "0.0.0.0", port: int = 8765) -> None:
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), MobileBridgeHandler)
    server.serve_forever()
