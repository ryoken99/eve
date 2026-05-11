from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from tools.research_scheduler import log_web_research_event, update_web_research_job
from tools.web_research import run_web_research_report


def run_job(job_path: str | Path) -> dict:
    path = Path(job_path)
    job = json.loads(path.read_text(encoding="utf-8"))
    update_web_research_job(path, status="running", started_at=datetime.now().isoformat(timespec="seconds"))
    result = run_web_research_report(
        str(job["query"]),
        max_pages=int(job.get("max_pages") or 8),
        open_visible_browser=bool(job.get("open_visible_browser", True)),
    )
    ok = result.get("status") == "ok" and len(result.get("report", {}).get("source_facts", [])) >= 2
    status = "completed" if ok else "failed"
    update_web_research_job(path, status=status, result=result, verification={"ok": ok, "min_sources": 2})
    log_web_research_event(status, {"job_path": str(path), "result": result, "verification": {"ok": ok, "min_sources": 2}})
    if not ok:
        raise RuntimeError("Web research did not collect enough independent sources.")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a scheduled Eve web research job.")
    parser.add_argument("--job", required=True)
    args = parser.parse_args()
    try:
        run_job(args.job)
        return 0
    except Exception as exc:
        path = Path(args.job)
        if path.exists():
            update_web_research_job(path, status="failed", error={"type": type(exc).__name__, "message": str(exc)})
        log_web_research_event("failed", {"job_path": args.job, "error": {"type": type(exc).__name__, "message": str(exc)}})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
