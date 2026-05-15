from __future__ import annotations

import re
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from autonomy.cron_manager import add_cron_job, list_cron_jobs
from core.paths import EVE_ROOT, LOGS_DIR, MEMORY_DIR, ensure_project_dirs
from dream.consolidation_schema import (
    ConsolidationDecision,
    ConsolidationInput,
    ConsolidationReport,
    ConsolidationSignal,
    ConsolidationSignalType,
)
from memory.diary_manager import read_diary, today_key


KEYWORDS = {
    "memory": ["memoria", "memória", "lembrar", "diario", "diário", "consolidar"],
    "skills": ["skill", "skills", "aprender", "procedimento"],
    "computer_control": ["rato", "teclado", "browser", "ecra", "ecrã", "screenshot", "ui"],
    "admin": ["admin", "permissao", "permissão", "elevada"],
    "self_improvement": ["melhorar", "auto", "recursive", "rollback", "lab"],
    "research": ["pesquisa", "tecnologia", "openai", "anthropic", "google", "meta", "xai"],
}

CONSOLIDATION_JOB_NAME = "Eve Diary Consolidation"

SIGNAL_HINTS = {
    ConsolidationSignalType.FACT: ["sou ", "tenho ", "moro", "nasci", "trabalho"],
    ConsolidationSignalType.PREFERENCE: ["gosto", "adoro", "prefiro", "quero", "odeio"],
    ConsolidationSignalType.PROJECT_UPDATE: ["projeto", "projecto", "eve", "helix", "repo", "github"],
    ConsolidationSignalType.TASK: ["agenda", "faz", "cria", "corrige", "pesquisa", "posta"],
    ConsolidationSignalType.ERROR: ["erro", "falhou", "falha", "nao fez", "não fez", "bug"],
    ConsolidationSignalType.IDEA: ["ideia", "podia", "devia", "melhorar", "evoluir"],
    ConsolidationSignalType.RELATIONSHIP: ["marta", "bubu", "raton", "mestre", "familia"],
    ConsolidationSignalType.TECHNICAL_DECISION: ["decisao", "decisão", "arquitectura", "schema", "daemon", "cron"],
    ConsolidationSignalType.FUTURE_FOLLOWUP: ["depois", "amanha", "amanhã", "mais tarde", "proximo", "próximo"],
}


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [p.strip() for p in parts if len(p.strip()) > 12]


def _signal_type(sentence: str) -> ConsolidationSignalType:
    lowered = sentence.lower()
    for signal_type, hints in SIGNAL_HINTS.items():
        if any(hint in lowered for hint in hints):
            return signal_type
    return ConsolidationSignalType.FACT


def _destination(signal_type: ConsolidationSignalType, importance: float, recurrence: float) -> str:
    if signal_type in {ConsolidationSignalType.ERROR, ConsolidationSignalType.TASK, ConsolidationSignalType.FUTURE_FOLLOWUP}:
        return "medium_term"
    if signal_type in {ConsolidationSignalType.PREFERENCE, ConsolidationSignalType.RELATIONSHIP} and importance + recurrence >= 1.15:
        return "long_term"
    if signal_type in {ConsolidationSignalType.TECHNICAL_DECISION, ConsolidationSignalType.PROJECT_UPDATE} and importance >= 0.65:
        return "medium_term"
    return "short_term"


def build_consolidation_report(day: str, diary: str) -> ConsolidationReport:
    sentences = _sentences(diary)
    counts = Counter(sentence.lower() for sentence in sentences)
    signals: list[ConsolidationSignal] = []
    decisions: list[ConsolidationDecision] = []
    for index, sentence in enumerate(sentences):
        signal_type = _signal_type(sentence)
        recurrence = min(1.0, counts[sentence.lower()] / 3)
        user_value = 0.8 if signal_type in {ConsolidationSignalType.PREFERENCE, ConsolidationSignalType.ERROR, ConsolidationSignalType.TECHNICAL_DECISION} else 0.55
        importance = min(1.0, 0.45 + recurrence + (0.25 if signal_type != ConsolidationSignalType.FACT else 0.0))
        confidence = 0.7 if len(sentence) > 25 else 0.5
        destination = _destination(signal_type, importance, recurrence)
        signal = ConsolidationSignal(
            signal_id=f"{day}-{index:04d}",
            type=signal_type,
            text=sentence,
            source="diary",
            importance=round(importance, 3),
            recurrence=round(recurrence, 3),
            user_value=round(user_value, 3),
            confidence=round(confidence, 3),
            memory_destination=destination,
            tags=[],
        )
        signals.append(signal)
        decisions.append(
            ConsolidationDecision(
                signal_id=signal.signal_id,
                decision="store" if importance >= 0.5 else "ignore",
                destination=destination,
                reason=f"{signal_type.value} signal with importance={signal.importance}, recurrence={signal.recurrence}",
                confidence=signal.confidence,
            )
        )
    return ConsolidationReport(
        day=day,
        input=ConsolidationInput(day=day, transcript_paths=[]),
        signals=signals,
        decisions=decisions,
        summary=f"Structured consolidation found {len(signals)} signals and {len(decisions)} memory decisions.",
        generated_at=datetime.now().isoformat(timespec="seconds"),
    )


def consolidate(day: str | None = None) -> Path:
    ensure_project_dirs()
    day = day or today_key()
    diary = read_diary(day)
    out = MEMORY_DIR / "medium_term" / f"daily_summary_{day}.md"
    candidates = MEMORY_DIR / "long_term" / "candidate_memories.md"
    log_path = LOGS_DIR / "autonomy" / "diary_consolidation_runs.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not diary.strip():
        out.write_text(f"# Daily Summary {day}\n\nNo diary entries yet.\n", encoding="utf-8")
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"day": day, "status": "empty", "summary": str(out), "generated_at": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False) + "\n")
        return out

    sentences = _sentences(diary)
    structured_report = build_consolidation_report(day, diary)
    hits: dict[str, list[str]] = {name: [] for name in KEYWORDS}
    for sentence in sentences:
        lowered = sentence.lower()
        for name, words in KEYWORDS.items():
            if any(word in lowered for word in words):
                hits[name].append(sentence)

    word_counts = Counter(re.findall(r"[A-Za-zÀ-ÿ0-9_]{4,}", diary.lower()))
    common = [word for word, _ in word_counts.most_common(20)]

    lines = [
        f"# Daily Summary {day}",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Signals By Theme",
        "",
    ]
    for theme, values in hits.items():
        lines.append(f"### {theme}")
        if values:
            for value in values[-8:]:
                lines.append(f"- {value}")
        else:
            lines.append("- No strong signal.")
        lines.append("")

    lines.extend(["## Frequent Terms", "", ", ".join(common), ""])
    lines.extend(["## Structured Memory Decisions", ""])
    for decision in structured_report.decisions[-20:]:
        signal = next((item for item in structured_report.signals if item.signal_id == decision.signal_id), None)
        text = signal.text if signal else decision.signal_id
        lines.append(f"- {decision.destination}: {text} ({decision.reason})")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")

    json_out = MEMORY_DIR / "medium_term" / f"daily_summary_{day}.json"
    json_out.write_text(json.dumps(structured_report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    candidate_jsonl = MEMORY_DIR / "long_term" / "candidate_memories.jsonl"
    with candidate_jsonl.open("a", encoding="utf-8") as handle:
        for signal, decision in zip(structured_report.signals, structured_report.decisions):
            if decision.decision == "store" and decision.destination in {"medium_term", "long_term"}:
                handle.write(json.dumps({"signal": signal.to_dict(), "decision": decision.to_dict()}, ensure_ascii=False) + "\n")

    with candidates.open("a", encoding="utf-8") as fh:
        promoted = 0
        fh.write(f"\n## Candidates from {day}\n\n")
        for theme, values in hits.items():
            for value in values[-3:]:
                fh.write(f"- [{theme}] {value}\n")
                promoted += 1
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "day": day,
                    "status": "ok",
                    "summary": str(out),
                    "structured_summary": str(json_out),
                    "candidate_memory_jsonl": str(candidate_jsonl),
                    "candidate_memory": str(candidates),
                    "themes": {theme: len(values) for theme, values in hits.items()},
                    "promoted_candidates": promoted,
                    "generated_at": datetime.now().isoformat(timespec="seconds"),
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    return out


def ensure_diary_consolidation_schedule(*, schedule: str = "6h") -> dict:
    existing = [job for job in list_cron_jobs() if job.get("name") == CONSOLIDATION_JOB_NAME]
    if existing:
        return {"status": "exists", "job": existing[0]}
    job = add_cron_job(CONSOLIDATION_JOB_NAME, schedule, f"Set-Location {EVE_ROOT}; python scripts\\diary_consolidation.py", enabled=True)
    return {"status": "created", "job": job}
