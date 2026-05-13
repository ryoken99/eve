from __future__ import annotations

import json
import re
from pathlib import Path

from core.paths import STATE_DIR, ensure_project_dirs


PERMISSIONS_PATH = STATE_DIR / "app_permissions.json"
DEFAULT_POLICY = {
    "chrome.exe": {"can_click": True, "can_type": True, "requires_submit_confirmation": True},
    "msedge.exe": {"can_click": True, "can_type": True, "requires_submit_confirmation": True},
    "notepad.exe": {"can_click": True, "can_type": True},
    "code.exe": {"can_click": True, "can_type": True},
    "powershell.exe": {"can_click": False, "can_type": False, "blocked": True},
    "anydesk.exe": {"blocked": True},
}
SENSITIVE_RE = re.compile(r"(bank|banco|paypal|stripe|password|senha|login|payment|checkout|submit|publish|send|postar|enviar)", re.I)


def load_app_permissions() -> dict:
    ensure_project_dirs()
    if not PERMISSIONS_PATH.exists():
        save_app_permissions(DEFAULT_POLICY)
        return dict(DEFAULT_POLICY)
    try:
        policy = json.loads(PERMISSIONS_PATH.read_text(encoding="utf-8"))
    except Exception:
        policy = {}
    return {**DEFAULT_POLICY, **policy}


def save_app_permissions(policy: dict) -> Path:
    PERMISSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PERMISSIONS_PATH.write_text(json.dumps(policy, indent=2, ensure_ascii=False), encoding="utf-8")
    return PERMISSIONS_PATH


def app_policy(app_name: str | None) -> dict:
    name = (app_name or "").lower()
    policy = load_app_permissions()
    return policy.get(name, {"blocked": True, "reason": "app has no explicit permission"})


def is_sensitive_action(action: str, selector: dict | str | None = None, text: str | None = None) -> bool:
    payload = " ".join(str(part or "") for part in (action, selector, text))
    return bool(SENSITIVE_RE.search(payload))


def check_app_permission(app_name: str | None, action: str, *, selector: dict | str | None = None, text: str | None = None, confirmed: bool = False) -> dict:
    policy = app_policy(app_name)
    if policy.get("blocked"):
        return {"allowed": False, "reason": policy.get("reason", "app blocked"), "policy": policy}
    if action in {"click", "invoke"} and not policy.get("can_click", False):
        return {"allowed": False, "reason": "click not permitted for app", "policy": policy}
    if action in {"type", "fill"} and not policy.get("can_type", False):
        return {"allowed": False, "reason": "typing not permitted for app", "policy": policy}
    if is_sensitive_action(action, selector, text) and (policy.get("requires_submit_confirmation", True)) and not confirmed:
        return {"allowed": False, "reason": "sensitive action requires confirmation", "policy": policy, "confirmation_required": True}
    return {"allowed": True, "policy": policy}
