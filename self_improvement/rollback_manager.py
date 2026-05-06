from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from core.paths import BACKUPS_DIR, EVE_ROOT, ensure_project_dirs
from security.audit_log import log_event


def _inside_eve(path: Path) -> bool:
    root = EVE_ROOT.resolve()
    target = path.resolve()
    return target == root or root in target.parents


def backup_file(path: str | Path, reason: str = "") -> Path | None:
    ensure_project_dirs()
    source = Path(path).resolve()
    if not source.exists() or not source.is_file():
        return None
    if not _inside_eve(source):
        raise PermissionError("Rollback manager only backs up files inside D:\\Eve")
    rel = source.relative_to(EVE_ROOT.resolve())
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUPS_DIR / "files" / stamp / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": str(source),
        "backup": str(dest),
        "reason": reason,
    }
    (dest.parent / f"{dest.name}.meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    log_event("file_backup_created", meta)
    return dest
