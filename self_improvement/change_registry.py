from __future__ import annotations

import json
from datetime import datetime, timezone

from core.paths import STATE_DIR, ensure_project_dirs


REGISTRY_PATH = STATE_DIR / "self_improvement_changes.json"


def record_change(change: dict) -> dict:
    ensure_project_dirs()
    rows = []
    if REGISTRY_PATH.exists():
        try:
            rows = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except Exception:
            rows = []
    row = {"timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), **change}
    rows.append(row)
    REGISTRY_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return row
