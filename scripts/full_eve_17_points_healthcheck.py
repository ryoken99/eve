from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from runtime_validation_lib import EVE_ROOT, LAB_DIR, check, detect_pc, finalize, now_iso, score_checks, write_health_state


SCRIPT_PLAN = [
    (0, "Environment", "check_pc_runtime_environment.py", None),
    (1, "Admin runtime", "test_admin_runtime.py", 6.8),
    (2, "Transcripts runtime", "test_transcript_channels.py", 7.4),
    (3, "Consolidation runtime", "test_diary_consolidation_runtime.py", 6.6),
    (4, "Layered memory runtime", "test_memory_layers.py", 7.0),
    (5, "Vector memory runtime", "test_vector_memory_runtime.py", 4.8),
    (6, "Dream runtime", "test_dream_cycle_runtime.py", 5.2),
    (7, "Awareness runtime", "test_awareness_runtime.py", 6.2),
    (8, "Personality runtime", "test_personality_runtime.py", 5.5),
    (9, "Lab runtime", "test_lab_runtime.py", 6.4),
    (10, "Errors and terminal runtime", "test_errors_terminal_runtime.py", 7.0),
    (11, "Daily research runtime", "test_daily_research_runtime.py", 5.8),
    (12, "Research to lab runtime", "test_research_to_lab_runtime.py", 5.4),
    (13, "Learning separation runtime", "test_learning_router_runtime.py", 5.9),
    (14, "Autonomous improvement runtime", "test_autonomous_improvement_runtime.py", 6.0),
    (15, "Computer use runtime", "test_computer_use_vnext_runtime.py", 5.9),
    (16, "ARSI runtime", "test_arsi_runtime.py", 5.7),
    (17, "Autonomy runtime", "test_full_autonomy_runtime.py", 6.5),
]


def run_script(script: str, *, timeout: int = 240) -> dict:
    started = time.perf_counter()
    path = EVE_ROOT / "scripts" / script
    try:
        completed = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(EVE_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "script": script,
            "returncode": None,
            "duration_seconds": round(time.perf_counter() - started, 3),
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": f"timeout after {timeout}s",
            "parsed": None,
            "score": 0.0,
            "passed": False,
            "timeout": True,
        }
    parsed = None
    stdout = completed.stdout.strip()
    if stdout:
        try:
            start = stdout.find("{")
            end = stdout.rfind("}")
            if start >= 0 and end >= start:
                parsed = json.loads(stdout[start : end + 1])
        except Exception:
            parsed = None
    parsed_summary = None
    if parsed:
        failed_checks = [
            {"name": item.get("name"), "evidence": item.get("evidence")}
            for item in parsed.get("checks", [])
            if not item.get("passed")
        ]
        parsed_summary = {
            "name": parsed.get("name"),
            "score": parsed.get("score"),
            "passed": parsed.get("passed"),
            "log": parsed.get("log"),
            "report": parsed.get("report"),
            "check_count": len(parsed.get("checks", [])),
            "failed_checks": failed_checks[:5],
        }
    return {
        "script": script,
        "returncode": completed.returncode,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "parsed": parsed_summary,
        "score": (parsed or {}).get("score", 0.0),
        "passed": completed.returncode == 0 and bool((parsed or {}).get("checks")),
    }


def optional_telegram_bridge_status() -> dict:
    """Return Telegram bridge status without affecting the 17-point score."""
    started = time.perf_counter()
    path = EVE_ROOT / "scripts" / "check_telegram_bridge.py"
    if not path.exists():
        return {
            "available": False,
            "running": False,
            "warning": "scripts/check_telegram_bridge.py is not present",
            "duration_seconds": round(time.perf_counter() - started, 3),
        }
    try:
        completed = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(EVE_ROOT),
            capture_output=True,
            text=True,
            timeout=45,
        )
    except Exception as exc:
        return {
            "available": True,
            "running": False,
            "warning": f"{type(exc).__name__}: {exc}",
            "duration_seconds": round(time.perf_counter() - started, 3),
        }
    parsed = None
    try:
        stdout = completed.stdout.strip()
        start = stdout.find("{")
        end = stdout.rfind("}")
        if start >= 0 and end >= start:
            parsed = json.loads(stdout[start : end + 1])
    except Exception:
        parsed = None
    return {
        "available": True,
        "returncode": completed.returncode,
        "running": bool((parsed or {}).get("running")),
        "pid": (parsed or {}).get("pid"),
        "last_update": (parsed or {}).get("last_update"),
        "token_configured": bool(((parsed or {}).get("token") or {}).get("configured")),
        "warning": None
        if completed.returncode == 0 and bool((parsed or {}).get("running"))
        else "Telegram bridge is not running or status check returned a warning",
        "status": parsed,
        "stderr_tail": completed.stderr[-1000:],
        "duration_seconds": round(time.perf_counter() - started, 3),
    }


def write_final_report(payload: dict) -> Path:
    lines = [
        "# Eve 17 Points Runtime Healthcheck",
        "",
        f"Generated: {payload['timestamp']}",
        f"Environment: `{payload['environment']}`",
        f"Overall runtime score: **{payload['overall_score']}/10**",
        "",
        "| Point | Area | Before | Runtime | Passed | Evidence |",
        "|---:|---|---:|---:|---|---|",
    ]
    for row in payload["points"]:
        parsed = row.get("parsed") or {}
        report = parsed.get("report", "")
        before = "" if row.get("before_score") is None else row.get("before_score")
        lines.append(
            f"| {row['point']} | {row['title']} | {before} | {row['score']} | {row['passed']} | `{report}` |"
        )
    lines.extend(["", "## Failures", ""])
    failures = [row for row in payload["points"] if not row["passed"] or float(row["score"] or 0) < 8.6]
    if not failures:
        lines.append("- None.")
    for row in failures:
        lines.append(f"- Point {row['point']} {row['title']}: score={row['score']} returncode={row['returncode']}")
        if row.get("stderr_tail"):
            lines.append(f"  - stderr: `{row['stderr_tail'][:500]}`")
    telegram = payload.get("telegram_bridge_status") or {}
    lines.extend(
        [
            "",
            "## Optional Telegram Bridge",
            "",
            f"- Available: `{telegram.get('available')}`",
            f"- Running: `{telegram.get('running')}`",
            f"- PID: `{telegram.get('pid')}`",
            f"- Last update: `{telegram.get('last_update')}`",
            f"- Token configured: `{telegram.get('token_configured')}`",
            f"- Warning: `{telegram.get('warning')}`",
        ]
    )
    path = LAB_DIR / "reports" / "eve_17_points_healthcheck.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> dict:
    rows = []
    for point, title, script, before in SCRIPT_PLAN:
        timeout = 720 if point == 17 else 300
        result = run_script(script, timeout=timeout)
        rows.append({"point": point, "title": title, "before_score": before, **result})
    point_rows = [row for row in rows if row["point"] != 0]
    overall = round(sum(float(row.get("score") or 0.0) for row in point_rows) / max(1, len(point_rows)), 2)
    payload = {
        "timestamp": now_iso(),
        "environment": detect_pc(),
        "overall_score": overall,
        "target_score": 8.6,
        "all_points_at_target": all(float(row.get("score") or 0.0) >= 8.6 for row in point_rows),
        "points": rows,
    }
    payload["telegram_bridge_status"] = optional_telegram_bridge_status()
    payload["state_path"] = str(write_health_state(payload))
    payload["report_path"] = str(write_final_report(payload))
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    return payload


if __name__ == "__main__":
    main()
