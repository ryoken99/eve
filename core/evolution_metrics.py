from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from autonomy.capability_roadmap import capability_audit
from core.paths import LAB_DIR, LOGS_DIR, MEMORY_DIR, ensure_project_dirs


def _today() -> datetime:
    return datetime.now()


def _day_file_key(day: datetime | None = None) -> str:
    return (day or _today()).strftime("%d-%m-%y")


def _iso_day(day: datetime | None = None) -> str:
    return (day or _today()).strftime("%Y-%m-%d")


def _files_changed_today(root: Path, *, patterns: tuple[str, ...] = ("*",), day: datetime | None = None) -> int:
    if not root.exists():
        return 0
    target = (day or _today()).date()
    count = 0
    for pattern in patterns:
        for path in root.rglob(pattern):
            if path.is_file() and datetime.fromtimestamp(path.stat().st_mtime).date() == target:
                count += 1
    return count


def _jsonl_lines_today(path: Path, *, day: datetime | None = None) -> int:
    if not path.exists():
        return 0
    target_prefix = (day or _today()).strftime("%Y-%m-%d")
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if target_prefix in line:
            count += 1
    return count


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def collect_evolution_metrics() -> dict[str, Any]:
    ensure_project_dirs()
    now = _today()
    day_file = _day_file_key(now)
    iso_day = _iso_day(now)
    audit = capability_audit()
    points = audit.get("points", [])
    weakest = sorted(points, key=lambda item: (float(item.get("score_10", 0)), int(item.get("id", 999))))[:3]

    transcript_root = LOGS_DIR / "transcripts"
    transcripts_created_today = _files_changed_today(transcript_root, patterns=(f"{day_file}.jsonl",), day=now)
    diary_path = MEMORY_DIR / "diary" / f"{iso_day}.md"
    errors_path = MEMORY_DIR / "errors" / "error_memory.jsonl"
    research_today = _files_changed_today(MEMORY_DIR / "technology" / "daily", day=now) + _files_changed_today(
        MEMORY_DIR / "world" / "daily", day=now
    )
    lab_today = _files_changed_today(LAB_DIR / "candidate_improvements", patterns=("*.json",), day=now)
    improvements_today = _files_changed_today(LAB_DIR / "candidate_improvements", patterns=("*.json",), day=now)
    applied_today = _files_changed_today(LAB_DIR / "candidate_improvements" / "verified_updates", day=now)
    autonomy_cycles = _jsonl_lines_today(LOGS_DIR / "autonomy" / f"{iso_day}.jsonl", day=now)

    resolved_errors = 0
    if errors_path.exists():
        for line in errors_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                item = json.loads(line)
            except Exception:
                continue
            if str(item.get("timestamp", "")).startswith(iso_day) and bool(item.get("resolved")):
                resolved_errors += 1

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "transcripts_created_today": transcripts_created_today,
        "diary_entries_today": _count_lines(diary_path),
        "memory_files_changed_today": _files_changed_today(MEMORY_DIR, day=now),
        "errors_recorded_today": _jsonl_lines_today(errors_path, day=now),
        "errors_resolved_today": resolved_errors,
        "research_items_today": research_today,
        "lab_candidates_today": lab_today,
        "improvements_proposed_today": improvements_today,
        "improvements_applied_today": applied_today,
        "autonomy_cycles_today": autonomy_cycles,
        "capability_average_score": audit.get("summary", {}).get("average_score_10"),
        "weakest_capability_points": [
            {"id": item.get("id"), "title": item.get("title"), "score_10": item.get("score_10")}
            for item in weakest
        ],
    }


def write_evolution_metrics_report() -> Path:
    metrics = collect_evolution_metrics()
    day = _iso_day()
    report_dir = MEMORY_DIR / "medium_term" / "evolution_metrics"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{day}.md"
    lines = [
        f"# Evolution Metrics {day}",
        "",
        f"Generated: {metrics['generated_at']}",
        "",
    ]
    for key, value in metrics.items():
        if key == "generated_at":
            continue
        lines.append(f"- `{key}`: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
