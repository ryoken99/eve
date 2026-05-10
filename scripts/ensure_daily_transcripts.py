from __future__ import annotations

import json
import sys
from pathlib import Path

EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from memory.daily_transcripts import ensure_daily_transcript_files


if __name__ == "__main__":
    print(json.dumps(ensure_daily_transcript_files(), indent=2, ensure_ascii=False))
