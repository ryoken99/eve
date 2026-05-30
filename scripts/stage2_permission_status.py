from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.permission_manager import list_pending_permission_requests, permission_status_summary


def main() -> int:
    payload = permission_status_summary()
    payload["pending_requests"] = list_pending_permission_requests()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
