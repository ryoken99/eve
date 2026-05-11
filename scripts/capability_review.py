from __future__ import annotations

import json
import sys
from pathlib import Path

EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from autonomy.capability_goal_harness import run_capability_goal_harness


def main() -> int:
    harness = run_capability_goal_harness(ensure_schedules=True, write_report=True)
    print(
        json.dumps(
            {
                "status": "ok",
                "harness": harness,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
