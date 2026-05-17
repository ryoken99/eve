from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVE_ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT_BASE = EVE_ROOT / "memory" / "transcripts"
RAW_TRANSCRIPT_ROOT = TRANSCRIPT_BASE / "raw"
MEMORY_DAY_OVERRIDE_PATH = EVE_ROOT / "memory" / "runtime" / "session_state" / "memory_day_override.json"
CHANNEL_PATHS = {
    "terminal": RAW_TRANSCRIPT_ROOT / "terminal",
    "telegram": RAW_TRANSCRIPT_ROOT / "telegram",
    "webui": RAW_TRANSCRIPT_ROOT / "webui",
    "system": RAW_TRANSCRIPT_ROOT / "system",
    "tools": TRANSCRIPT_BASE / "tools",
    "errors": TRANSCRIPT_BASE / "errors",
}

SECRET_PATTERNS = [
    re.compile(r"(?i)(token|secret|api[_-]?key|password|pass)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)(bearer)\s+([a-z0-9._\-]+)"),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _memory_day() -> tuple[str, dict[str, Any] | None]:
    if MEMORY_DAY_OVERRIDE_PATH.exists():
        try:
            payload = json.loads(MEMORY_DAY_OVERRIDE_PATH.read_text(encoding="utf-8"))
        except Exception:
            payload = None
        if isinstance(payload, dict) and payload.get("enabled") is True:
            active_day = str(payload.get("active_memory_day") or "").strip()
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", active_day):
                return active_day, payload
    return datetime.now().strftime("%Y-%m-%d"), None


def _sanitize_message(message: str) -> str:
    text = str(message or "")
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1)}=[REDACTED]", text)
    return text


def write_transcript(channel: str, speaker: str, message: str, metadata: dict[str, Any] | None = None) -> Path:
    safe_channel = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(channel or "system")).strip("._") or "system"
    safe_speaker = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(speaker or "system")).strip("._") or "system"
    root = CHANNEL_PATHS.get(safe_channel, RAW_TRANSCRIPT_ROOT / safe_channel)
    memory_day, override = _memory_day()
    path = root / f"{memory_day}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    final_metadata = dict(metadata or {})
    final_metadata.setdefault("real_timestamp", _now_iso())
    final_metadata.setdefault("memory_day", memory_day)
    if override:
        final_metadata.setdefault(
            "memory_day_override",
            {
                "enabled": True,
                "previous_memory_day": override.get("previous_memory_day"),
                "reason": override.get("reason"),
                "created_at": override.get("created_at"),
            },
        )
    entry = {
        "timestamp": _now_iso(),
        "channel": safe_channel,
        "speaker": safe_speaker,
        "message": _sanitize_message(message),
        "metadata": final_metadata,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def write_user_message(channel: str, message: str, metadata: dict[str, Any] | None = None) -> Path:
    return write_transcript(channel, "sandro", message, metadata or {})


def write_eve_message(channel: str, message: str, metadata: dict[str, Any] | None = None) -> Path:
    return write_transcript(channel, "eve", message, metadata or {})


def write_tool_event(tool_name: str, action: str, result_summary: str, metadata: dict[str, Any] | None = None) -> Path:
    payload = {"tool_name": tool_name, "action": action, **(metadata or {})}
    return write_transcript("tools", "system", result_summary, payload)


def write_error_event(error_type: str, error_message: str, metadata: dict[str, Any] | None = None) -> Path:
    payload = {"error_type": error_type, **(metadata or {})}
    return write_transcript("errors", "system", error_message, payload)


def write_system_event(event_type: str, message: str, metadata: dict[str, Any] | None = None) -> Path:
    payload = {"event_type": event_type, **(metadata or {})}
    return write_transcript("system", "system", message, payload)
