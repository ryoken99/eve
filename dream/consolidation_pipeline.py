from __future__ import annotations

import re
from datetime import datetime, timezone


def consolidate_diary_text(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    facts, decisions, tasks, preferences, contradictions = [], [], [], [], []
    for line in lines:
        lower = line.lower()
        if any(word in lower for word in ("decidi", "decision", "decisão", "decisao")):
            decisions.append(line)
        elif any(word in lower for word in ("todo", "tarefa", "pendente", "fazer")):
            tasks.append(line)
        elif any(word in lower for word in ("gosto", "prefiro", "interesse", "preference")):
            preferences.append(line)
        elif re.search(r"\b(mas|contradiz|conflito|inconsistente)\b", lower):
            contradictions.append(line)
        else:
            facts.append(line)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "facts": facts,
        "decisions": decisions,
        "tasks": tasks,
        "preferences": preferences,
        "contradictions": contradictions,
        "memory_moves": [],
        "confidence": 0.8 if lines else 0.0,
    }
