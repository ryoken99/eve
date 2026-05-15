from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


TRANSCRIPT_CHANNELS = (
    "chat",
    "console",
    "interface",
    "tools",
    "actions",
    "errors",
    "autonomy",
    "dream",
    "research",
    "arsi",
)


@dataclass(frozen=True)
class TranscriptEvent:
    event_id: str
    timestamp: str
    channel: str
    source: str
    target: str
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    session_id: str = "main"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_transcript_event(event: TranscriptEvent | dict[str, Any]) -> dict[str, Any]:
    if isinstance(event, TranscriptEvent):
        data = event.as_dict()
    else:
        data = dict(event)
    channel = str(data.get("channel") or data.get("kind") or "chat")
    if channel not in TRANSCRIPT_CHANNELS:
        channel = "actions"
    return {
        "event_id": str(data.get("event_id") or f"evt_{uuid.uuid4().hex}"),
        "timestamp": str(data.get("timestamp") or _now()),
        "channel": channel,
        "source": str(data.get("source") or "unknown"),
        "target": str(data.get("target") or "Eve"),
        "role": str(data.get("role") or data.get("source") or "event"),
        "content": str(data.get("content") or ""),
        "metadata": dict(data.get("metadata") or {}),
        "tags": list(data.get("tags") or []),
        "session_id": str(data.get("session_id") or "main"),
    }
