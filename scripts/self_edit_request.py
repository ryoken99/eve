from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.self_edit_engine import execute_self_edit_request


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a controlled Stage 2 self-edit request.")
    parser.add_argument("request", nargs="+", help="Self-improvement request text.")
    parser.add_argument("--dry-run", action="store_true", help="Plan/check without applying allowlisted edits.")
    parser.add_argument("--request-id", help="Specific permission request/grant id to use.")
    parser.add_argument("--apply-authorized", action="store_true", help="Apply an already authorized medium/high self-edit.")
    args = parser.parse_args()
    result = execute_self_edit_request(
        " ".join(args.request),
        dry_run=args.dry_run,
        apply_authorized=args.apply_authorized,
        request_id=args.request_id,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"applied", "dry_run", "permission_required", "blocked", "authorized_dry_run", "authorized_proposal_only"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
