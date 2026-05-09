from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.capability_self_test import collect_capability_self_test
from core.paths import EVE_ROOT, LOGS_DIR, STATE_DIR, ensure_project_dirs
from security.safety_modes import current_safety_mode


def _tail(path: Path, lines: int = 80) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:]


def build_diagnostics_bundle(note: str = "") -> dict[str, Any]:
    from core.eve_tool_registry import TOOLS

    ensure_project_dirs()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = LOGS_DIR / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "note": note,
        "eve_root": str(EVE_ROOT),
        "safety_mode": current_safety_mode(),
        "capabilities": collect_capability_self_test(),
        "tool_count": len(TOOLS),
        "tools": sorted(TOOLS),
        "recent_audit": _tail(LOGS_DIR / "audit" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"),
        "recent_errors": _tail(LOGS_DIR / "errors" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"),
    }
    manifest_path = out_dir / f"diagnostics_{stamp}.json"
    zip_path = out_dir / f"diagnostics_{stamp}.zip"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(manifest_path, manifest_path.name)
        for candidate in (STATE_DIR / "eve_status.json", STATE_DIR / "task_ledger.jsonl"):
            if candidate.exists():
                archive.write(candidate, f"state/{candidate.name}")
    return {"manifest": str(manifest_path), "zip": str(zip_path), "summary": {"tool_count": len(TOOLS), "safety_mode": current_safety_mode()}}
