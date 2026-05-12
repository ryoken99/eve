from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from core.paths import LAB_DIR, MEMORY_DIR, ensure_project_dirs
from core.self_report import functional_self_report
from dream.memory_reorganizer import dream_memory_decisions, run_dream
from memory.semantic_vector.vector_store import rebuild_memory_index


PROMOTION_RULES = {
    "short_term": ["tarefa actual", "erro recente", "ficheiros em edicao", "janela activa"],
    "medium_term": ["projectos activos", "skills em teste", "decisoes recentes", "padroes recentes"],
    "long_term": ["preferencias estaveis", "missao", "constituicao", "regras de seguranca", "correccoes importantes"],
    "archive_only": ["conversa casual", "duplicados", "ruido", "informacao expirada"],
}


def run_dream_cycle(day: str | None = None) -> dict:
    """Run the operational dream cycle: consolidate, report, reindex and queue lab ideas."""
    ensure_project_dirs()
    report_path = run_dream(day)
    index_path = rebuild_memory_index()
    dream_reports_dir = MEMORY_DIR / "dream_reports"
    dream_reports_dir.mkdir(parents=True, exist_ok=True)
    mirror_path = dream_reports_dir / report_path.name
    mirror_path.write_text(report_path.read_text(encoding="utf-8"), encoding="utf-8")
    memory_decisions = dream_memory_decisions(mirror_path.read_text(encoding="utf-8"))

    self_report = functional_self_report("dream_cycle")
    queue_path = LAB_DIR / "queue" / f"dream_cycle_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "dream_report": str(report_path),
        "memory_report": str(mirror_path),
        "vector_index": str(index_path),
        "promotion_rules": PROMOTION_RULES,
        "memory_decisions": memory_decisions,
        "self_report": self_report,
        "lab_candidates": [
            "avaliar se o sonho promoveu apenas memoria estavel",
            "testar persona_stability_checks contra a constituicao da Eve",
            "verificar erros recorrentes antes de criar novas skills",
        ],
    }
    queue_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload | {"queue": str(queue_path)}


def latest_dream_cycle_queue() -> Path | None:
    queue_dir = LAB_DIR / "queue"
    if not queue_dir.exists():
        return None
    rows = sorted(queue_dir.glob("dream_cycle_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return rows[0] if rows else None
