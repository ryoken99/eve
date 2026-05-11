from __future__ import annotations

import argparse
import sys
from pathlib import Path

EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from autonomy.daemon import daemon_tick, request_daemon_stop, run_daemon


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()
    if args.stop:
        print(request_daemon_stop())
        return 0
    if args.once:
        print(daemon_tick())
        return 0
    run_daemon(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
