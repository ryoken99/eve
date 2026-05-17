from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.self_awareness_answer import answer_self_awareness_question


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="+")
    args = parser.parse_args()
    print(answer_self_awareness_question(" ".join(args.question)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
