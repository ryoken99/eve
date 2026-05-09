from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from core.paths import STATE_DIR, ensure_project_dirs


PENDING_INTENT_PATH = STATE_DIR / "pending_intent.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_pending_intent() -> dict | None:
    if not PENDING_INTENT_PATH.exists():
        return None
    try:
        payload = json.loads(PENDING_INTENT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def save_pending_intent(intent: dict) -> Path:
    ensure_project_dirs()
    payload = dict(intent)
    payload.setdefault("created_at", _now())
    PENDING_INTENT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return PENDING_INTENT_PATH


def clear_pending_intent(reason: str = "") -> None:
    if PENDING_INTENT_PATH.exists():
        PENDING_INTENT_PATH.unlink()


def pending_intent_context() -> str:
    intent = load_pending_intent()
    if not intent:
        return "Nenhuma intencao pendente."
    return json.dumps(intent, indent=2, ensure_ascii=False)[:3000]


def extract_x_post_draft(user_prompt: str, assistant_text: str) -> str | None:
    combined = f"{user_prompt}\n{assistant_text}".lower()
    if not any(term in combined for term in (" x ", "x.com", "twitter", "post", "publica")):
        return None

    quoted_lines = []
    for line in assistant_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            quoted_lines.append(stripped.lstrip("> ").strip())
    if quoted_lines:
        return "\n".join(line for line in quoted_lines if line).strip() or None

    bold_matches = re.findall(r"\*\*([^*]{12,280})\*\*", assistant_text)
    for candidate in reversed(bold_matches):
        if any(term in candidate.lower() for term in ("not just", "eve", "local agent", "chat")):
            return candidate.strip()

    marker = "not just a chat anymore"
    idx = assistant_text.lower().find(marker)
    if idx >= 0:
        sentence = assistant_text[idx:].splitlines()[0].strip(" .")
        return sentence if sentence else None
    return None


def maybe_save_x_post_draft(user_prompt: str, assistant_text: str) -> Path | None:
    text = extract_x_post_draft(user_prompt, assistant_text)
    if not text:
        return None
    return save_pending_intent(
        {
            "type": "x_post_draft",
            "text": text,
            "platform": "x",
            "awaiting": "publish_or_schedule_confirmation",
            "source": "assistant_draft",
            "updated_at": _now(),
        }
    )

