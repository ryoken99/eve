from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.heartbeat_tracker import write_startup_event


if __name__ == "__main__":
    print(json.dumps(write_startup_event(), ensure_ascii=False, indent=2))
