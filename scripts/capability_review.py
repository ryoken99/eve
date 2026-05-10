from __future__ import annotations

import json
import sys
from pathlib import Path

EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from autonomy.autonomy_director import run_autonomy_cycle
from autonomy.autonomous_executor import execute_autonomous_backlog
from autonomy.capability_roadmap import append_capability_review_history, write_capability_audit


def main() -> int:
    audit_path = write_capability_audit()
    history_path = append_capability_review_history()
    cycle = run_autonomy_cycle(
        triggers=["capability_review"],
        max_new_missions=1,
        call_llm="auto",
        cycle_name="scheduled_capability_review",
    )
    execution = execute_autonomous_backlog(max_missions=1, notify_chat=True)
    print(
        json.dumps(
            {
                "status": "ok",
                "audit": str(audit_path),
                "history": str(history_path),
                "cycle": cycle,
                "execution": execution,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
