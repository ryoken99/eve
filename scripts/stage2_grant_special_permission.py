from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.permission_manager import grant_special_permission


def main() -> int:
    parser = argparse.ArgumentParser(description="Grant a critical Stage 2 special one-shot permission.")
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--granted-by", default="Sandro")
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--expires-minutes", type=int, default=30)
    args = parser.parse_args()
    result = grant_special_permission(args.request_id, args.granted_by, args.confirm, args.expires_minutes)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
