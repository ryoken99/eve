from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.paths import LAB_DIR, MEMORY_DIR, ensure_project_dirs
from dream.diary_consolidator import consolidate
from memory.diary_manager import today_key


def run_dream(day: str | None = None) -> Path:
    ensure_project_dirs()
    day = day or today_key()
    summary_path = consolidate(day)
    summary = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
    report_dir = LAB_DIR / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / f"dream_{day}.md"
    lines = [
        f"# Dream Report {day}",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Inputs",
        "",
        f"- Summary: {summary_path}",
        "- Long-term memory",
        "- Candidate memories",
        "- Error memory",
        "",
        "## Patterns",
        "",
    ]
    if "computer_control" in summary:
        lines.append("- Computer-control remains a recurring desired capability.")
    if "self_improvement" in summary:
        lines.append("- Self-improvement must stay lab-first with rollback.")
    if "memory" in summary:
        lines.append("- Memory and diary remain foundational.")
    if len(lines) < 18:
        lines.append("- Not enough signal yet; continue collecting diary entries.")
    lines.extend(
        [
            "",
            "## Lab Ideas",
            "",
            "- Compare plain-text memory retrieval with future vector retrieval.",
            "- Test better summaries for diary consolidation.",
            "- Build approval flow before UI/admin tools.",
            "",
            "## Proposed Memory Moves",
            "",
            "- Keep stable user requirements in long-term memory.",
            "- Keep daily operational notes in medium-term memory.",
            "- Keep active task state in short-term memory.",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report
