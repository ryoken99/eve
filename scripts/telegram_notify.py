from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.telegram_bridge import STATE_PATH, send_message, telegram_token


def _load_chat_id() -> int | str | None:
    if not STATE_PATH.exists():
        return None
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    return state.get("last_chat_id")


def notify(text: str) -> dict[str, Any]:
    if not text.strip():
        return {"ok": False, "error": "message is empty"}
    chat_id = _load_chat_id()
    if not chat_id:
        return {
            "ok": False,
            "error": "No Telegram chat_id is known yet. Send a message to Eve on Telegram first.",
            "chat_id_present": False,
        }
    try:
        token = telegram_token()
        result = send_message(chat_id, text, token=token)
    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "chat_id_present": True,
        }
    return {
        "ok": True,
        "chat_id_present": True,
        "message_id": result.get("message_id"),
        "text_preview": text[:120],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a safe Eve system notification over Telegram.")
    parser.add_argument("message", nargs="+")
    args = parser.parse_args()
    payload = notify(" ".join(args.message))
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
