from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any

from core.paths import ensure_project_dirs, EVE_ROOT


VAULT_PATH = EVE_ROOT / "secrets" / "vault.json"


def _load() -> dict[str, Any]:
    ensure_project_dirs()
    if not VAULT_PATH.exists():
        return {}
    try:
        return json.loads(VAULT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict[str, Any]) -> None:
    VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VAULT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def mask_secret(value: str, *, keep: int = 4) -> str:
    if len(value) <= keep * 2:
        return "*" * len(value)
    return value[:keep] + "*" * (len(value) - keep * 2) + value[-keep:]


def store_secret(name: str, value: str, *, note: str = "") -> dict[str, Any]:
    data = _load()
    encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
    data[name] = {
        "value_b64": encoded,
        "masked": mask_secret(value),
        "note": note,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    _save(data)
    return {"name": name, "masked": data[name]["masked"], "note": note}


def get_secret(name: str, *, reveal: bool = False) -> dict[str, Any]:
    item = _load().get(name)
    if not item:
        raise KeyError(name)
    if reveal:
        return {"name": name, "value": base64.b64decode(item["value_b64"]).decode("utf-8"), "masked": item["masked"]}
    return {"name": name, "masked": item["masked"], "note": item.get("note", "")}


def list_secrets() -> list[dict[str, Any]]:
    return [{"name": name, "masked": item.get("masked"), "note": item.get("note", "")} for name, item in _load().items()]

