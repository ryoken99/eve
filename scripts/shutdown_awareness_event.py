from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.heartbeat_tracker import write_shutdown_event


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reason", default="manual")
    args = parser.parse_args()
    print(json.dumps(write_shutdown_event(args.reason), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
