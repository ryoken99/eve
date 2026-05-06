from __future__ import annotations

from pathlib import Path

from core.paths import WORKSPACE_DIR, ensure_project_dirs


def workspace_snapshot() -> dict:
    ensure_project_dirs()
    files = []
    for path in WORKSPACE_DIR.rglob("*"):
        if path.is_file():
            files.append({"path": str(path.relative_to(WORKSPACE_DIR)), "size": path.stat().st_size})
    return {"workspace": str(WORKSPACE_DIR), "files": files}
