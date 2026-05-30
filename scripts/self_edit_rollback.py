from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.self_edit_engine import rollback_change


def main() -> int:
    parser = argparse.ArgumentParser(description="Rollback a Stage 2 self-edit by change id.")
    parser.add_argument("--change-id", required=True)
    args = parser.parse_args()
    result = rollback_change(args.change_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
