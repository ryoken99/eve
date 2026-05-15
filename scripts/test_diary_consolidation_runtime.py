from __future__ import annotations

from runtime_validation_lib import check, finalize

from core.paths import LOGS_DIR, MEMORY_DIR, ensure_project_dirs
from dream.diary_consolidator import consolidate
from memory.diary_manager import append_chat, today_key


def main() -> dict:
    ensure_project_dirs()
    day = today_key()
    samples = [
        "Preferencia: Sandro gosta de anime e game dev narrativo.",
        "Tarefa: testar consolidacao runtime varias vezes por dia.",
        "Erro recente: OCR falhou e deve virar licao.",
        "Projeto ativo: Eve 17 pontos runtime validation.",
        "Decisao tecnica: usar UIA e DOM antes de OCR.",
    ]
    for sample in samples:
        append_chat("runtime", sample, tags=["runtime_consolidation"])
    summary_path = consolidate(day)
    summary = summary_path.read_text(encoding="utf-8")
    candidates = MEMORY_DIR / "long_term" / "candidate_memories.md"
    log_path = LOGS_DIR / "autonomy" / "diary_consolidation_runs.jsonl"
    checks = [
        check("consolidation markdown exists", summary_path.exists(), str(summary_path), critical=True),
        check("summary contains project and error signals", "self_improvement" in summary or "computer_control" in summary or "memory" in summary, summary[:1000], critical=True),
        check("candidate memories file exists", candidates.exists(), str(candidates), critical=True),
        check("autonomy consolidation log exists", log_path.exists(), str(log_path), critical=True),
    ]
    return finalize("point_03_consolidation_runtime", "Point 03 Diary Consolidation Runtime", "point_03_consolidation_runtime.md", checks)


if __name__ == "__main__":
    main()
