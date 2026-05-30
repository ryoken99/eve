from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.permission_manager import deny_permission

parser = argparse.ArgumentParser()
parser.add_argument("--request-id", required=True)
parser.add_argument("--denied-by", default="Sandro")
parser.add_argument("--reason", default="")
args = parser.parse_args()
print(json.dumps(deny_permission(args.request_id, args.denied_by, args.reason), ensure_ascii=False, indent=2))
