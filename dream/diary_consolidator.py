from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs
from memory.diary_manager import read_diary, today_key


KEYWORDS = {
    "memory": ["memoria", "memória", "lembrar", "diario", "diário", "consolidar"],
    "skills": ["skill", "skills", "aprender", "procedimento"],
    "computer_control": ["rato", "teclado", "browser", "ecra", "ecrã", "screenshot", "ui"],
    "admin": ["admin", "permissao", "permissão", "elevada"],
    "self_improvement": ["melhorar", "auto", "recursive", "rollback", "lab"],
    "research": ["pesquisa", "tecnologia", "openai", "anthropic", "google", "meta", "xai"],
}


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [p.strip() for p in parts if len(p.strip()) > 12]


def consolidate(day: str | None = None) -> Path:
    ensure_project_dirs()
    day = day or today_key()
    diary = read_diary(day)
    out = MEMORY_DIR / "medium_term" / f"daily_summary_{day}.md"
    candidates = MEMORY_DIR / "long_term" / "candidate_memories.md"
    if not diary.strip():
        out.write_text(f"# Daily Summary {day}\n\nNo diary entries yet.\n", encoding="utf-8")
        return out

    sentences = _sentences(diary)
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
    out.write_text("\n".join(lines), encoding="utf-8")

    with candidates.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## Candidates from {day}\n\n")
        for theme, values in hits.items():
            for value in values[-3:]:
                fh.write(f"- [{theme}] {value}\n")
    return out
