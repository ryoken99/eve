from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from continual_learning_common import CL_ROOT, date_paths, ensure_cl_dirs, excerpt, item_text, read_jsonl, read_text


FEEDBACK_PATTERNS = [
    "estas robotica",
    "estás robótica",
    "isso esta errado",
    "isso está errado",
    "nao confundas",
    "não confundas",
    "o nome certo e eve",
    "o nome certo é eve",
    "isso e lore",
    "isso é lore",
    "isso e real",
    "isso é real",
    "guarda isto",
    "nao facas isso",
    "não faças isso",
    "funcionou",
    "passou no teste",
]


def default_date() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def load_day(date_key: str) -> dict:
    paths = date_paths(date_key)
    channels = {
        "terminal": read_jsonl(paths["terminal"]),
        "telegram": read_jsonl(paths["telegram"]),
        "webui": read_jsonl(paths["webui"]),
        "tools": read_jsonl(paths["tools"]),
        "errors": read_jsonl(paths["errors"]),
    }
    return {
        "date": date_key,
        "paths": paths,
        "rollup": read_text(paths["rollup"]),
        "candidates": read_jsonl(paths["candidates"]),
        "dream": read_text(paths["dream"]),
        "channels": channels,
    }


def detect_feedback(day: dict) -> list[dict]:
    findings = []
    for channel, rows in day["channels"].items():
        for item in rows:
            text = item_text(item)
            lowered = text.lower()
            for pattern in FEEDBACK_PATTERNS:
                if pattern in lowered:
                    findings.append({"channel": channel, "pattern": pattern, "excerpt": excerpt(text)})
    return findings


def detect_tasks(day: dict) -> list[str]:
    tasks: list[str] = []
    task_re = re.compile(r"\b(vamos|precisamos|falta|todo|tarefa|pr[oó]ximo|next)\b", re.IGNORECASE)
    for channel, rows in day["channels"].items():
        for item in rows:
            text = item_text(item)
            if task_re.search(text):
                tasks.append(f"{channel}: {excerpt(text, 180)}")
    return tasks[:20]


def possible_improvements(day: dict, feedback: list[dict]) -> list[dict]:
    improvements: list[dict] = []
    if feedback:
        improvements.append(
            {
                "problem": "Sandro feedback or correction detected.",
                "evidence": "; ".join(item["excerpt"] for item in feedback[:3]),
                "proposed_fix": "Review style/memory rules and create a targeted improvement candidate.",
                "risk": "low",
                "requires_approval": False,
            }
        )
    if day["channels"]["errors"]:
        improvements.append(
            {
                "problem": "Errors were recorded during the day.",
                "evidence": "; ".join(excerpt(item_text(item), 160) for item in day["channels"]["errors"][:3]),
                "proposed_fix": "Create a technical backlog item with reproduction and test plan.",
                "risk": "medium",
                "requires_approval": True,
            }
        )
    if day["channels"]["tools"]:
        improvements.append(
            {
                "problem": "Tool usage occurred and may contain lessons.",
                "evidence": f"{len(day['channels']['tools'])} tool events recorded.",
                "proposed_fix": "Review tool outcomes and add procedural lessons if useful.",
                "risk": "low",
                "requires_approval": False,
            }
        )
    if not improvements:
        improvements.append(
            {
                "problem": "No strong improvement signal detected.",
                "evidence": "Daily transcripts, rollup and dream were reviewed deterministically.",
                "proposed_fix": "Keep monitoring; no change proposed today.",
                "risk": "low",
                "requires_approval": False,
            }
        )
    return improvements


def build_report(day: dict) -> tuple[str, dict]:
    feedback = detect_feedback(day)
    tasks = detect_tasks(day)
    improvements = possible_improvements(day, feedback)
    counts = {name: len(rows) for name, rows in day["channels"].items()}
    errors = [excerpt(item_text(item), 220) for item in day["channels"]["errors"][:20]]
    tools = [excerpt(item_text(item), 220) for item in day["channels"]["tools"][:20]]
    conflicts = []
    for item in day["candidates"]:
        text = json.dumps(item, ensure_ascii=False).lower()
        if "conflict" in text or "conflito" in text:
            conflicts.append(excerpt(json.dumps(item, ensure_ascii=False), 220))
    lines = [
        f"# Eve Daily Experience Analysis - {day['date']}",
        "",
        "## Sources",
        f"- rollup exists: {bool(day['rollup'])}",
        f"- dream exists: {bool(day['dream'])}",
        f"- candidates: {len(day['candidates'])}",
        "",
        "## Channel Counts",
    ]
    for name, count in counts.items():
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Feedback From Sandro"])
    lines.extend([f"- {item['channel']}: {item['excerpt']}" for item in feedback] or ["- none detected"])
    lines.extend(["", "## Errors Detected"])
    lines.extend([f"- {item}" for item in errors] or ["- none detected"])
    lines.extend(["", "## Tools Used"])
    lines.extend([f"- {item}" for item in tools] or ["- none detected"])
    lines.extend(["", "## Memory Conflicts"])
    lines.extend([f"- {item}" for item in conflicts] or ["- none detected"])
    lines.extend(["", "## Pending/Future Tasks"])
    lines.extend([f"- {item}" for item in tasks] or ["- none detected"])
    lines.extend(["", "## Possible Improvements"])
    for item in improvements:
        lines.extend(
            [
                f"- Problem: {item['problem']}",
                f"  Evidence: {item['evidence']}",
                f"  Proposed fix: {item['proposed_fix']}",
                f"  Risk: {item['risk']}",
                f"  Requires approval: {item['requires_approval']}",
            ]
        )
    summary = {"feedback": feedback, "tasks": tasks, "improvements": improvements, "counts": counts, "conflicts": conflicts}
    return "\n".join(lines) + "\n", summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Eve daily experience deterministically.")
    parser.add_argument("--date", default=default_date(), help="Date YYYY-MM-DD")
    args = parser.parse_args()
    ensure_cl_dirs()
    day = load_day(args.date)
    report, summary = build_report(day)
    output = CL_ROOT / "daily_analysis" / f"{args.date}_experience_analysis.md"
    output.write_text(report, encoding="utf-8")
    print(json.dumps({"ok": True, "date": args.date, "path": str(output), **summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
