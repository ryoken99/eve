from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import permission_manager
from core.self_edit_engine import execute_self_edit_request


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a Stage 2.2 self-edit with an existing one-shot grant.")
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--special", action="store_true", help="Apply with a critical special grant if the request is critical.")
    args = parser.parse_args()
    request = permission_manager.get_permission_request(args.request_id) or {}
    text = request.get("request_text") or f"Apply authorized self-edit {args.request_id}"
    result = execute_self_edit_request(text, dry_run=args.dry_run, apply_authorized=True, request_id=args.request_id, special=args.special)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"applied", "authorized_dry_run", "rolled_back_after_failed_tests"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
