from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.permission_manager import grant_permission

parser = argparse.ArgumentParser()
parser.add_argument("--request-id", required=True)
parser.add_argument("--granted-by", default="Sandro")
parser.add_argument("--expires-minutes", type=int, default=60)
args = parser.parse_args()
print(json.dumps(grant_permission(args.request_id, args.granted_by, expires_minutes=args.expires_minutes), ensure_ascii=False, indent=2))
