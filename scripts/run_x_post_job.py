from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from learning.skill_manager import run_skill
from tools.x_scheduler import log_x_post_event, update_x_post_job


def run_job(job_path: str | Path) -> dict:
    path = Path(job_path)
    job = json.loads(path.read_text(encoding="utf-8"))
    update_x_post_job(path, status="running")
    result = run_skill(
        job.get("skill") or "trusted/x_publish_text_learning",
        args={"url": job["url"], "text": job["text"]},
        approved=True,
    )
    update_x_post_job(path, status="completed", result=result)
    log_x_post_event("completed", {"job_path": str(path), "result": result})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a scheduled Eve X post job.")
    parser.add_argument("--job", required=True)
    args = parser.parse_args()
    try:
        run_job(args.job)
        return 0
    except Exception as exc:
        path = Path(args.job)
        if path.exists():
            update_x_post_job(path, status="failed", error={"type": type(exc).__name__, "message": str(exc)})
        log_x_post_event("failed", {"job_path": args.job, "error": {"type": type(exc).__name__, "message": str(exc)}})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
