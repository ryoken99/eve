from __future__ import annotations

import importlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.paths import EVE_ROOT, LAB_DIR, LOGS_DIR, STATE_DIR, ensure_project_dirs


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def detect_pc() -> dict[str, Any]:
    root = EVE_ROOT.resolve()
    drive = root.drive.upper()
    if str(root).lower() == r"d:\eve".lower():
        pc = "PC1"
    elif str(root).lower() == r"e:\eve".lower():
        pc = "PC2"
    else:
        pc = "custom"
    return {"pc": pc, "root": str(root), "drive": drive, "expected_pc1": r"D:\Eve", "expected_pc2": r"E:\eve"}


def check(name: str, passed: bool, evidence: Any = None, *, critical: bool = False) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "critical": bool(critical), "evidence": evidence}


def module_available(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", None)
        return {"name": name, "available": True, "version": str(version) if version else None}
    except Exception as exc:
        return {"name": name, "available": False, "error": str(exc)}


def run_step(name: str, func: Callable[[], Any], *, critical: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        evidence = func()
        if isinstance(evidence, dict) and "passed" in evidence:
            passed = bool(evidence["passed"])
        else:
            passed = bool(evidence) if isinstance(evidence, bool) else True
        return check(name, passed, evidence, critical=critical) | {"duration_seconds": round(time.perf_counter() - started, 3)}
    except Exception as exc:
        return check(name, False, {"error": type(exc).__name__, "message": str(exc)}, critical=critical) | {"duration_seconds": round(time.perf_counter() - started, 3)}


def score_checks(checks: list[dict[str, Any]]) -> float:
    if not checks:
        return 0.0
    weights = [2 if item.get("critical") else 1 for item in checks]
    earned = sum(weight for item, weight in zip(checks, weights) if item.get("passed"))
    return round((earned / sum(weights)) * 10, 2)


def log_runtime(name: str, payload: dict[str, Any]) -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "runtime" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def append_runtime_jsonl(name: str, payload: dict[str, Any]) -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "runtime" / f"{name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def write_point_report(filename: str, title: str, checks: list[dict[str, Any]], summary: dict[str, Any] | None = None) -> Path:
    ensure_project_dirs()
    score = score_checks(checks)
    lines = [
        f"# {title}",
        "",
        f"Generated: {now_iso()}",
        f"EVE_ROOT: `{EVE_ROOT}`",
        f"Runtime score: **{score}/10**",
        "",
        "## Checks",
        "",
    ]
    for item in checks:
        status = "PASS" if item.get("passed") else "FAIL"
        critical = " critical" if item.get("critical") else ""
        lines.append(f"- **{status}**{critical}: {item.get('name')}")
        evidence = item.get("evidence")
        if evidence is not None:
            preview = json.dumps(evidence, ensure_ascii=False, default=str)
            if len(preview) > 1200:
                preview = preview[:1200] + "...(truncated)"
            lines.append(f"  - evidence: `{preview}`")
    if summary:
        lines.extend(["", "## Summary", "", "```json", json.dumps(summary, indent=2, ensure_ascii=False, default=str), "```"])
    path = LAB_DIR / "reports" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def finalize(name: str, title: str, report_filename: str, checks: list[dict[str, Any]], summary: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "name": name,
        "title": title,
        "timestamp": now_iso(),
        "environment": detect_pc(),
        "score": score_checks(checks),
        "passed": all(item.get("passed") for item in checks if item.get("critical")),
        "checks": checks,
        "summary": summary or {},
    }
    payload["log"] = str(log_runtime(name, payload))
    payload["report"] = str(write_point_report(report_filename, title, checks, summary=summary))
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    return payload


def powershell(command: str, *, timeout: int = 60) -> dict[str, Any]:
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=str(EVE_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def write_health_state(payload: dict[str, Any]) -> Path:
    ensure_project_dirs()
    path = STATE_DIR / "eve_17_points_healthcheck.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def runtime_imports() -> dict[str, Any]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "modules": {
            name: module_available(name)
            for name in ("playwright", "pyautogui", "uiautomation", "PIL", "pytesseract")
        },
    }
