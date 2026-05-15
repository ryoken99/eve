from __future__ import annotations

import json
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import LOGS_DIR, ensure_project_dirs


TRANSCRIPT_TYPES = ("chat", "console", "interface", "tools", "actions", "errors", "autonomy", "dream", "research", "arsi")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def transcript_date_key(day: datetime | None = None) -> str:
    return (day or datetime.now()).strftime("%d/%m/%y")


def transcript_file_key(day: datetime | None = None) -> str:
    return (day or datetime.now()).strftime("%d-%m-%y")


def transcript_path(kind: str, day: datetime | None = None) -> Path:
    if kind not in TRANSCRIPT_TYPES:
        raise ValueError(f"Tipo de transcricao invalido: {kind}")
    ensure_project_dirs()
    root = Path(os.environ.get("EVE_TRANSCRIPTS_DIR") or (LOGS_DIR / "transcripts"))
    path = root / kind / f"{transcript_file_key(day)}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def ensure_daily_transcript_files(day: datetime | None = None) -> dict[str, str]:
    paths = {}
    for kind in TRANSCRIPT_TYPES:
        path = transcript_path(kind, day)
        if not path.exists():
            path.write_text("", encoding="utf-8")
        paths[kind] = str(path)
    return paths


def _last_transcript_hash(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return ""
    chunk_size = 8192
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        end = handle.tell()
        offset = max(0, end - chunk_size)
        handle.seek(offset)
        data = handle.read().decode("utf-8", errors="replace")
    for line in reversed(data.splitlines()):
        if line.strip():
            try:
                return json.loads(line).get("hash", "")
            except Exception:
                return ""
    return ""


def append_transcript(kind: str, event: str, payload: dict[str, Any], *, day: datetime | None = None) -> dict[str, Any]:
    path = transcript_path(kind, day)
    previous_hash = _last_transcript_hash(path)
    entry = {
        "timestamp": now_iso(),
        "date_key": transcript_date_key(day),
        "kind": kind,
        "event": event,
        "payload": payload,
        "previous_hash": previous_hash,
    }
    raw = json.dumps({"previous_hash": previous_hash, "entry": {key: value for key, value in entry.items() if key != "hash"}}, sort_keys=True, ensure_ascii=False)
    entry["hash"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def append_console_transcript(text: object, *, stream: str = "stdout", event: str = "console_output") -> dict[str, Any]:
    return append_transcript("console", event, {"stream": stream, "text": str(text)})


def append_interface_transcript(source: str, target: str, content: str, *, tags: list[str] | None = None) -> dict[str, Any]:
    return append_transcript(
        "interface",
        "interface_message",
        {"source": source, "target": target, "content": content, "tags": tags or []},
    )


def append_structured_transcript(event: dict[str, Any]) -> dict[str, Any]:
    from memory.transcript_schema import normalize_transcript_event

    normalized = normalize_transcript_event(event)
    return append_transcript(normalized["channel"], "structured_event", normalized)
