from __future__ import annotations

import json
import sys
from pathlib import Path

EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from dream.diary_consolidator import consolidate, ensure_diary_consolidation_schedule
from memory.vector_provider import rebuild_vector_memory


def main() -> int:
    summary = consolidate()
    vector = rebuild_vector_memory()
    schedule = ensure_diary_consolidation_schedule()
    print(json.dumps({"status": "ok", "summary": str(summary), "vector": vector, "schedule": schedule}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
