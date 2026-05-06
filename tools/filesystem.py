from __future__ import annotations

from pathlib import Path

from core.paths import WORKSPACE_DIR, ensure_project_dirs


def _safe_path(path: str | Path) -> Path:
    ensure_project_dirs()
    target = (WORKSPACE_DIR / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    root = WORKSPACE_DIR.resolve()
    if target != root and root not in target.parents:
        raise PermissionError(f"Filesystem access is limited to workspace: {root}")
    return target


def list_dir(path: str = ".") -> list[str]:
    target = _safe_path(path)
    if not target.exists():
        return []
    return sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir())


def read_file(path: str) -> str:
    target = _safe_path(path)
    return target.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> Path:
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def append_file(path: str, content: str) -> Path:
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(content)
        if not content.endswith("\n"):
            fh.write("\n")
    return target
