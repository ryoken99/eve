from __future__ import annotations

import argparse
import sys
from pathlib import Path

EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from tools.mobile_bridge import run_mobile_bridge_server


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    run_mobile_bridge_server(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
