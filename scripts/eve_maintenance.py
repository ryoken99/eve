from __future__ import annotations

import sys
from pathlib import Path

EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from dream.memory_reorganizer import run_dream
from memory.memory_manager import consolidate_today
from memory.semantic_vector.vector_store import rebuild_memory_index
from research.technology_watcher import run_technology_watch


def main() -> int:
    print(f"consolidated={consolidate_today()}")
    print(f"dream={run_dream()}")
    print(f"vector_index={rebuild_memory_index()}")
    print(f"technology_watch={run_technology_watch()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
