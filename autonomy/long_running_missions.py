from __future__ import annotations

import json
from datetime import datetime, timezone

from core.paths import STATE_DIR, ensure_project_dirs


def save_mission_checkpoint(mission_id: str, checkpoint: dict) -> dict:
    ensure_project_dirs()
    path = STATE_DIR / "mission_checkpoints" / f"{mission_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), **checkpoint}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {**row, "path": str(path)}
