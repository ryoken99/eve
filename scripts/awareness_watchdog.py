from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.awareness_engine import build_self_state, write_awareness_snapshot, write_self_state
from core.file_change_awareness import run_file_scan
from core.heartbeat_tracker import write_heartbeat

POLICY_PATH = ROOT / "memory" / "_system" / "awareness_watchdog_policy.yaml"


def _policy_enabled() -> bool:
    if not POLICY_PATH.exists():
        return False
    text = POLICY_PATH.read_text(encoding="utf-8", errors="replace").lower()
    return "enabled: true" in text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run one watchdog tick and exit.")
    parser.add_argument("--interval", type=int, default=300)
    args = parser.parse_args()
    if not args.once and not _policy_enabled():
        print(json.dumps({"ok": False, "running": False, "reason": "watchdog disabled by policy"}, indent=2))
        return 0

    while True:
        write_heartbeat("awareness_watchdog")
        state = build_self_state()
        write_self_state(state)
        write_awareness_snapshot(state)
        run_file_scan()
        print(json.dumps({"ok": True, "tick": state.get("timestamp")}, ensure_ascii=False))
        if args.once:
            return 0
        time.sleep(max(60, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
