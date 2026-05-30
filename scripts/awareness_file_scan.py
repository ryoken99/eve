from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.file_change_awareness import run_file_scan


if __name__ == "__main__":
    print(json.dumps(run_file_scan(), ensure_ascii=False, indent=2))
