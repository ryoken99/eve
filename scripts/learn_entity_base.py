from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from memory.entity_learning import learn_entity_base
from memory.semantic_vector.vector_store import rebuild_memory_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Learn from Eve external entity base memory.")
    parser.add_argument("--batch", type=int, default=25)
    parser.add_argument("--until-done", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    reset = args.reset
    while True:
        result = learn_entity_base(batch_size=args.batch, reset=reset)
        reset = False
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if not args.until_done or result["remaining"] <= 0:
            break
    print(f"vector_index={rebuild_memory_index()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
