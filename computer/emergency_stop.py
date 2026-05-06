from __future__ import annotations

from pathlib import Path

from core.paths import STATE_DIR, ensure_project_dirs


LOCK_PATH = STATE_DIR / "emergency_lock"


def enable_emergency_lock(reason: str = "") -> Path:
    ensure_project_dirs()
    LOCK_PATH.write_text(reason or "locked", encoding="utf-8")
    return LOCK_PATH


def clear_emergency_lock() -> None:
    if LOCK_PATH.exists():
        LOCK_PATH.unlink()


def emergency_locked() -> bool:
    return LOCK_PATH.exists()


def assert_not_locked() -> None:
    if emergency_locked():
        raise RuntimeError("Emergency lock ativo. Limpa com comando explicito antes de continuar.")
