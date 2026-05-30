from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta

from continual_learning_common import CL_ROOT, ensure_cl_dirs, excerpt, read_text, stable_id


LESSONS_PATH = CL_ROOT / "lessons" / "lessons_learned.md"


def default_date() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def category_for(line: str) -> str:
    q = line.lower()
    if "telegram" in q:
        return "telegram"
    if "webui" in q or "web ui" in q:
        return "webui"
    if "terminal" in q:
        return "terminal"
    if "erro" in q or "error" in q or "falha" in q:
        return "technical"
    if "tool" in q or "ferramenta" in q:
        return "tools"
    if "memoria" in q or "memory" in q or "conflict" in q:
        return "memory"
    if "robot" in q or "style" in q or "persona" in q or "tom" in q:
        return "style/persona"
    if "rollover" in q:
        return "rollover"
    if "private" in q or "token" in q or "secret" in q:
        return "privacy"
    if "codex" in q:
        return "codex_workflow"
    return "technical"


def extract_lessons(date_key: str, analysis: str) -> list[dict]:
    lessons: list[dict] = []
    for raw in analysis.splitlines():
        line = raw.strip(" -")
        if not line:
            continue
        low = line.lower()
        if low.startswith(("problem:", "evidence:", "proposed fix:", "risk:", "requires approval:")):
            continue
        if any(term in low for term in ("feedback", "error", "erro", "tool", "conflict", "conflito", "possible improvements", "problem")):
            lesson_text = "Review this daily signal and keep it available for future improvements."
            action = "Create or refine an improvement candidate if the signal repeats."
            if "robot" in low or "tom" in low:
                lesson_text = "In personal replies, Eve should sound natural before becoming technical."
                action = "Review the style layer and response examples."
            elif "erro" in low or "error" in low:
                lesson_text = "Technical errors should be converted into reproducible backlog items."
                action = "Create a testable technical candidate when enough evidence exists."
            elif "tool" in low:
                lesson_text = "Tool usage should be reviewed for procedural lessons and incomplete flows."
                action = "Add procedural lesson if the tool outcome teaches a repeatable step."
            category = category_for(line)
            lessons.append(
                {
                    "lesson_id": stable_id("lesson", date_key, category, lesson_text, line),
                    "date": date_key,
                    "category": category,
                    "evidence": excerpt(line),
                    "lesson": lesson_text,
                    "recommended_action": action,
                    "status": "active",
                }
            )
    unique: dict[str, dict] = {}
    for item in lessons:
        unique[item["lesson_id"]] = item
    return list(unique.values())[:20]


def append_lessons(lessons: list[dict]) -> int:
    ensure_cl_dirs()
    existing = read_text(LESSONS_PATH)
    additions = []
    for lesson in lessons:
        if lesson["lesson_id"] in existing:
            continue
        additions.extend(
            [
                "",
                f"## {lesson['date']} - {lesson['category']} - {lesson['lesson_id']}",
                "",
                f"- Data: {lesson['date']}",
                f"- Categoria: {lesson['category']}",
                f"- Evidencia: {lesson['evidence']}",
                f"- Licao: {lesson['lesson']}",
                f"- Accao recomendada: {lesson['recommended_action']}",
                f"- Status: {lesson['status']}",
            ]
        )
    if additions:
        with LESSONS_PATH.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(additions) + "\n")
    return len(additions) // 8


def main() -> int:
    parser = argparse.ArgumentParser(description="Update Eve continual learning lessons.")
    parser.add_argument("--date", default=default_date(), help="Date YYYY-MM-DD")
    args = parser.parse_args()
    analysis_path = CL_ROOT / "daily_analysis" / f"{args.date}_experience_analysis.md"
    analysis = read_text(analysis_path)
    lessons = extract_lessons(args.date, analysis)
    added = append_lessons(lessons)
    print(json.dumps({"ok": True, "date": args.date, "analysis": str(analysis_path), "lessons_seen": len(lessons), "lessons_added": added, "path": str(LESSONS_PATH)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
