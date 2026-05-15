from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from memory.daily_transcripts import append_transcript, transcript_path
from memory.transcript_schema import TRANSCRIPT_CHANNELS, normalize_transcript_event


def append_structured_transcript(event: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_transcript_event(event)
    return append_transcript(normalized["channel"], "structured_event", normalized)


def list_transcript_channels() -> list[str]:
    return list(TRANSCRIPT_CHANNELS)


def search_transcripts(query: str, *, channels: list[str] | None = None, limit: int = 20, day: datetime | None = None) -> list[dict[str, Any]]:
    terms = [term.lower() for term in query.split() if term.strip()]
    selected = channels or list(TRANSCRIPT_CHANNELS)
    rows: list[dict[str, Any]] = []
    for channel in selected:
        try:
            path = transcript_path(channel, day)
        except ValueError:
            continue
        if not path.exists():
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if not line.strip():
                continue
            lowered = line.lower()
            if terms and not all(term in lowered for term in terms):
                continue
            try:
                payload = json.loads(line)
            except Exception:
                payload = {"raw": line}
            rows.append({"channel": channel, "line": line_no, "path": str(path), "event": payload})
            if len(rows) >= limit:
                return rows
    return rows
