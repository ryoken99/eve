from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import LOGS_DIR, MEMORY_DIR, ensure_project_dirs
from lab.lab_manager import create_candidate
from memory.daily_transcripts import append_transcript
from memory.errors.error_schema import classify_error as classify_error_type, make_error_item
from security.audit_log import log_event


def error_memory_path() -> Path:
    ensure_project_dirs()
    return MEMORY_DIR / "errors" / "error_memory.jsonl"


def error_log_path() -> Path:
    ensure_project_dirs()
    return LOGS_DIR / "errors" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"


def record_error(source: str, task: str, error_type: str, error_text: str, *, lesson: str = "", resolved: bool = False) -> dict:
    if not error_type or error_type == "unknown":
        error_type = classify_error_type(error_text, source=source)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": source,
        "task": task,
        "error_type": error_type,
        "error_text": error_text[-8000:],
        "lesson": lesson,
        "resolved": resolved,
    }
    line = json.dumps(entry, ensure_ascii=False)
    with error_memory_path().open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    with error_log_path().open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    append_transcript("errors", "error_recorded", entry)
    if lesson or error_type.startswith("exit_"):
        title = f"error_{source}_{error_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        hypothesis = f"Erro em {source}/{task}: {error_type}. Lesson: {lesson or 'needs analysis'}"
        create_candidate(title, hypothesis, metric="error_recurrence_reduction")
    log_event("error_recorded", entry)
    return entry


def classify_error(message: str, *, source: str = "unknown") -> str:
    return classify_error_type(message, source=source)


def error_to_lesson(entry: dict) -> str:
    if entry.get("lesson"):
        return str(entry["lesson"])
    return f"Quando ocorrer {entry.get('error_type', 'erro')}, verificar causa, reproduzir e criar teste antes de repetir a acao."


def error_to_lab_candidate(entry: dict) -> dict:
    title = f"error_fix_{entry.get('source', 'unknown')}_{entry.get('error_type', 'unknown')}"
    hypothesis = error_to_lesson(entry)
    path = create_candidate(title, hypothesis, metric="error_recurrence_reduction")
    return {"path": str(path), "title": title, "hypothesis": hypothesis}


def known_fix_lookup(error_type: str) -> str:
    fixes = {
        "missing_dependency": "instalar dependencia no ambiente correto e atualizar requirements se for parte da Eve",
        "permission": "verificar admin_capability_status e pedir/usar elevacao auditada",
        "timeout": "aumentar timeout ou transformar em processo background com poll",
        "corrupt_or_empty_json": "tratar ficheiro vazio/corrompido com fallback e log",
        "verification_failed": "nao declarar sucesso; recolher evidencia e tentar recuperacao",
    }
    return fixes.get(error_type, "")


def recent_errors(limit: int = 20) -> list[dict]:
    path = error_memory_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out
