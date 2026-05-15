from __future__ import annotations

import sys
from pathlib import Path

EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from tools.telegram_bridge import main


if __name__ == "__main__":
    raise SystemExit(main())
