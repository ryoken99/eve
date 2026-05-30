from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


EVE_ROOT = Path(__file__).resolve().parents[1]
MEMORY_ROOT = EVE_ROOT / "memory"
CL_ROOT = MEMORY_ROOT / "continual_learning"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_cl_dirs() -> None:
    for path in [
        CL_ROOT / "daily_analysis",
        CL_ROOT / "lessons",
        CL_ROOT / "improvement_candidates",
        CL_ROOT / "codex_tasks",
        CL_ROOT / "approval_queue",
        CL_ROOT / "applied_changes",
        CL_ROOT / "rejected_changes",
        MEMORY_ROOT / "procedural" / "skills" / "definitions",
        MEMORY_ROOT / "procedural" / "skills" / "tests",
        MEMORY_ROOT / "procedural" / "skills" / "history",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                item = {"raw": line}
            if isinstance(item, dict):
                rows.append(item)
    return rows


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha1("\n".join(parts).encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def item_text(item: dict[str, Any]) -> str:
    for key in ("message", "content", "text", "result_summary", "error_message", "raw"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    metadata = item.get("metadata")
    if isinstance(metadata, dict):
        for key in ("message", "content", "summary", "error"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return json.dumps(item, ensure_ascii=False)[:500]


def excerpt(text: str, limit: int = 240) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    return compact[:limit]


def classify_category(text: str, source_channel: str = "") -> str:
    q = text.lower()
    if "telegram" in q or source_channel == "telegram":
        return "telegram"
    if "webui" in q or "web ui" in q or source_channel == "webui":
        return "webui"
    if source_channel == "terminal":
        return "terminal"
    if "rollover" in q:
        return "rollover"
    if "memoria" in q or "memória" in q or "retrieval" in q:
        return "memory"
    if "robot" in q or "tom" in q or "estilo" in q or "persona" in q:
        return "style/persona"
    if "erro" in q or "falha" in q or "bug" in q:
        return "technical"
    if source_channel == "tools":
        return "tools"
    if "privado" in q or "token" in q or "secret" in q:
        return "privacy"
    if "codex" in q:
        return "codex_workflow"
    return "technical"


def classify_risk(text: str, target_files: list[str] | None = None) -> tuple[str, bool]:
    joined = (text + " " + " ".join(target_files or [])).lower()
    if any(term in joined for term in ("secret", "token", "vault", "git push", "apagar", "delete", "scheduled task", "tarefa windows", "telegram bridge core", "web ui routing")):
        return "high", True
    if any(term in joined for term in ("retrieval", "rollover", "metadata", "novo script", "new script", "classificacao", "classificação")):
        return "medium", True
    return "low", False


def date_paths(date_key: str) -> dict[str, Path]:
    return {
        "rollup": MEMORY_ROOT / "transcripts" / "daily_rollups" / f"{date_key}_rollup.md",
        "candidates": MEMORY_ROOT / "_processed" / "classifications" / f"{date_key}_memory_candidates.jsonl",
        "dream": MEMORY_ROOT / "dreams" / "daily" / f"{date_key}_dream.md",
        "errors": MEMORY_ROOT / "transcripts" / "errors" / f"{date_key}.jsonl",
        "tools": MEMORY_ROOT / "transcripts" / "tools" / f"{date_key}.jsonl",
        "terminal": MEMORY_ROOT / "transcripts" / "raw" / "terminal" / f"{date_key}.jsonl",
        "telegram": MEMORY_ROOT / "transcripts" / "raw" / "telegram" / f"{date_key}.jsonl",
        "webui": MEMORY_ROOT / "transcripts" / "raw" / "webui" / f"{date_key}.jsonl",
    }
