from __future__ import annotations

from datetime import datetime

from memory.daily_transcripts import TRANSCRIPT_TYPES, transcript_path
from memory.transcript_validator import read_transcript_jsonl


def reconstruct_day(day: datetime | None = None) -> dict:
    events = []
    for kind in TRANSCRIPT_TYPES:
        for row in read_transcript_jsonl(transcript_path(kind, day)):
            events.append(row)
    events.sort(key=lambda row: row.get("timestamp", ""))
    return {"events": events, "count": len(events)}


def reconstruct_session(session_id: str, day: datetime | None = None) -> dict:
    rows = []
    for row in reconstruct_day(day)["events"]:
        payload = row.get("payload") or {}
        if payload.get("session_id") == session_id or row.get("session_id") == session_id:
            rows.append(row)
    return {"session_id": session_id, "events": rows, "count": len(rows)}


def find_missing_turns(day: datetime | None = None) -> dict:
    events = reconstruct_day(day)["events"]
    seen = {row.get("turn_id") or (row.get("payload") or {}).get("turn_id") for row in events}
    missing = []
    for row in events:
        parent = row.get("parent_turn_id") or (row.get("payload") or {}).get("parent_turn_id")
        if parent and parent not in seen:
            missing.append({"turn_id": row.get("turn_id"), "missing_parent": parent})
    return {"missing": missing, "ok": not missing}
