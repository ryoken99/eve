from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.permission_manager import list_pending_permission_requests

print(json.dumps({"pending": list_pending_permission_requests()}, ensure_ascii=False, indent=2))
