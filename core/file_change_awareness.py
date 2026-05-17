from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVE_ROOT = Path(__file__).resolve().parents[1]
AWARENESS_ROOT = EVE_ROOT / "memory" / "runtime" / "awareness"
STATE_PATH = AWARENESS_ROOT / "state" / "file_snapshot.json"
FILE_CHANGES_DIR = AWARENESS_ROOT / "file_changes"
CODE_CHANGES_DIR = AWARENESS_ROOT / "code_changes"

TRACKED_PATHS = [
    EVE_ROOT / "app",
    EVE_ROOT / "core",
    EVE_ROOT / "scripts",
    EVE_ROOT / "tools",
    EVE_ROOT / "memory" / "_system",
    EVE_ROOT / "memory" / "runtime" / "sessions",
    EVE_ROOT / "memory" / "runtime" / "awareness",
]

SKIP_PARTS = {".venv", "__pycache__", "vector", "transcripts", "logs", "chunks", ".git"}
HASH_MAX_BYTES = 512_000


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(EVE_ROOT))
    except Exception:
        return str(path)


def _should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & SKIP_PARTS)


def classify_file_change(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("app/") or normalized.startswith("core/"):
        return "code"
    if normalized.startswith("scripts/"):
        return "script"
    if normalized.startswith("tools/"):
        return "tool"
    if "memory/_system" in normalized:
        return "memory_system"
    if "memory/runtime" in normalized:
        return "memory_runtime"
    return "unknown"


def _hash_file(path: Path, size: int) -> str | None:
    if size > HASH_MAX_BYTES:
        return None
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return None


def scan_tracked_paths() -> dict[str, Any]:
    files: dict[str, Any] = {}
    for root in TRACKED_PATHS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or _should_skip(path):
                continue
            stat = path.stat()
            rel = _relative(path)
            files[rel] = {
                "path": rel,
                "size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                "extension": path.suffix.lower(),
                "category": classify_file_change(rel),
                "hash": _hash_file(path, stat.st_size),
            }
    return {"scanned_at": now_iso(), "file_count": len(files), "files": files}


def load_previous_file_snapshot() -> dict[str, Any]:
    try:
        if STATE_PATH.exists():
            return json.loads(STATE_PATH.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        pass
    return {"files": {}}


def write_file_snapshot(snapshot: dict[str, Any]) -> Path:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return STATE_PATH


def diff_file_snapshots(previous: dict[str, Any], current: dict[str, Any]) -> list[dict[str, Any]]:
    before = previous.get("files", {}) or {}
    after = current.get("files", {}) or {}
    changes: list[dict[str, Any]] = []
    for path, info in after.items():
        old = before.get(path)
        if not old:
            change_type = "created"
        elif old.get("size") != info.get("size") or old.get("modified_time") != info.get("modified_time") or old.get("hash") != info.get("hash"):
            change_type = "modified"
        else:
            continue
        changes.append({"detected_at": current.get("scanned_at"), "change_type": change_type, **info})
    for path, old in before.items():
        if path not in after:
            changes.append({"detected_at": current.get("scanned_at"), "change_type": "deleted", **old})
    return changes


def write_file_changes_jsonl(changes: list[dict[str, Any]]) -> dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")
    FILE_CHANGES_DIR.mkdir(parents=True, exist_ok=True)
    CODE_CHANGES_DIR.mkdir(parents=True, exist_ok=True)
    file_path = FILE_CHANGES_DIR / f"{today}_file_changes.jsonl"
    code_path = CODE_CHANGES_DIR / f"{today}_code_changes.jsonl"
    file_count = 0
    code_count = 0
    with file_path.open("a", encoding="utf-8") as file_handle, code_path.open("a", encoding="utf-8") as code_handle:
        for change in changes:
            row = json.dumps(change, ensure_ascii=False)
            file_handle.write(row + "\n")
            file_count += 1
            if change.get("category") in {"code", "script", "tool"}:
                code_handle.write(row + "\n")
                code_count += 1
    return {"file_changes_path": str(file_path), "code_changes_path": str(code_path), "file_changes": file_count, "code_changes": code_count}


def run_file_scan() -> dict[str, Any]:
    previous = load_previous_file_snapshot()
    current = scan_tracked_paths()
    changes = diff_file_snapshots(previous, current)
    write_file_snapshot(current)
    written = write_file_changes_jsonl(changes) if changes else {"file_changes": 0, "code_changes": 0}
    return {"ok": True, "scanned_files": current["file_count"], "changes": changes[:50], "change_count": len(changes), **written}
