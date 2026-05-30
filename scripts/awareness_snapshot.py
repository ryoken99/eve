from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.awareness_engine import build_self_state, write_awareness_report, write_awareness_snapshot, write_initial_audit_report, write_self_state


def main() -> int:
    state = build_self_state()
    self_state_path = write_self_state(state)
    snapshot_path = write_awareness_snapshot(state)
    report_path = write_awareness_report(state)
    initial_audit = write_initial_audit_report()
    summary = {
        "ok": True,
        "self_state": str(self_state_path),
        "snapshot": str(snapshot_path),
        "report": str(report_path),
        "initial_audit": str(initial_audit),
        "webui_ok": state.get("health_summary", {}).get("webui_ok"),
        "telegram_running": state.get("health_summary", {}).get("telegram_running"),
        "ollama_ok": state.get("health_summary", {}).get("ollama_ok"),
        "session_id": ((state.get("session") or {}).get("current_session") or {}).get("session_id"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
