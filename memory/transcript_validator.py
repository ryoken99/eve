from __future__ import annotations

import hashlib
import json
from pathlib import Path

from memory.daily_transcripts import TRANSCRIPT_TYPES, transcript_path


def transcript_hash(entry: dict, previous_hash: str = "") -> str:
    payload = {key: value for key, value in entry.items() if key not in {"hash", "previous_hash"}}
    raw = json.dumps({"previous_hash": previous_hash, "entry": payload}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_transcript_entry(entry: dict, previous_hash: str = "") -> dict:
    row = dict(entry)
    row.setdefault("previous_hash", previous_hash)
    row["hash"] = transcript_hash(row, row["previous_hash"])
    return row


def read_transcript_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def validate_transcript_chain(kind: str, *, path: Path | None = None) -> dict:
    if kind not in TRANSCRIPT_TYPES:
        raise ValueError(f"invalid transcript kind: {kind}")
    target = path or transcript_path(kind)
    rows = read_transcript_jsonl(target)
    previous = ""
    errors = []
    for index, row in enumerate(rows):
        if "hash" not in row:
            errors.append({"index": index, "reason": "missing hash"})
            previous = row.get("hash", previous)
            continue
        expected = transcript_hash(row, row.get("previous_hash", ""))
        if row.get("previous_hash", "") != previous:
            errors.append({"index": index, "reason": "previous hash mismatch"})
        if row["hash"] != expected:
            errors.append({"index": index, "reason": "hash mismatch"})
        previous = row["hash"]
    return {"valid": not errors, "path": str(target), "entries": len(rows), "errors": errors}
