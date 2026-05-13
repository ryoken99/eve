from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import EVE_ROOT, ensure_project_dirs


ACCOUNT_PATH = EVE_ROOT / "secrets" / "local_account.json"
DEFAULT_ITERATIONS = 260_000
LEGACY_ACCESS_CODE = "172099"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _hash_code(code: str, salt: bytes, iterations: int = DEFAULT_ITERATIONS) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", str(code).encode("utf-8"), salt, iterations)
    return _b64(digest)


def _safe_name(value: str) -> str:
    value = str(value or "").strip().lower()
    value = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)
    return value or "default"


def load_local_account() -> dict[str, Any]:
    if not ACCOUNT_PATH.exists():
        return {}
    return json.loads(ACCOUNT_PATH.read_text(encoding="utf-8"))


def save_local_account(payload: dict[str, Any]) -> None:
    ensure_project_dirs()
    ACCOUNT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACCOUNT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(ACCOUNT_PATH, 0o600)
    except OSError:
        pass


def set_access_code(code: str, *, overwrite: bool = False) -> dict[str, Any]:
    if not str(code or "").strip():
        raise ValueError("access code cannot be empty")
    account = load_local_account()
    if account.get("access_code") and not overwrite:
        return {"ok": True, "changed": False, "reason": "access code already configured"}
    salt = os.urandom(16)
    account["access_code"] = {
        "algorithm": "pbkdf2_sha256",
        "iterations": DEFAULT_ITERATIONS,
        "salt": _b64(salt),
        "hash": _hash_code(code, salt),
        "created_at": account.get("access_code", {}).get("created_at") or _now(),
        "updated_at": _now(),
    }
    account.setdefault("installations", [])
    account.setdefault("active_installation", "")
    save_local_account(account)
    return {"ok": True, "changed": True}


def verify_access_code(code: str) -> dict[str, Any]:
    account = load_local_account()
    configured = bool(account.get("access_code"))
    if not configured:
        ok = str(code or "").strip() == LEGACY_ACCESS_CODE
        return {
            "ok": ok,
            "configured": False,
            "legacy_fallback": True,
            "installations": list_installations(),
            "active_installation": active_installation(),
        }
    data = account["access_code"]
    salt = base64.b64decode(data["salt"])
    expected = str(data["hash"])
    actual = _hash_code(code, salt, int(data.get("iterations") or DEFAULT_ITERATIONS))
    ok = hmac.compare_digest(actual, expected)
    return {
        "ok": ok,
        "configured": True,
        "legacy_fallback": False,
        "installations": list_installations(),
        "active_installation": active_installation(),
    }


def upsert_installation(name: str, root: str | Path, *, make_active: bool = False) -> dict[str, Any]:
    account = load_local_account()
    installations = list(account.get("installations") or [])
    clean_name = _safe_name(name)
    root_path = str(Path(root).expanduser())
    record = {
        "name": clean_name,
        "label": str(name or clean_name).strip() or clean_name,
        "root": root_path,
        "updated_at": _now(),
    }
    replaced = False
    for index, item in enumerate(installations):
        if _safe_name(item.get("name", "")) == clean_name:
            record["created_at"] = item.get("created_at") or _now()
            installations[index] = record
            replaced = True
            break
    if not replaced:
        record["created_at"] = _now()
        installations.append(record)
    account["installations"] = installations
    if make_active or not account.get("active_installation"):
        account["active_installation"] = clean_name
    save_local_account(account)
    return {"ok": True, "installation": record, "active_installation": account.get("active_installation")}


def list_installations() -> list[dict[str, Any]]:
    account = load_local_account()
    active = str(account.get("active_installation") or "")
    rows: list[dict[str, Any]] = []
    for item in account.get("installations") or []:
        row = dict(item)
        root = Path(str(row.get("root") or ""))
        row["active"] = _safe_name(row.get("name", "")) == active
        row["current_root"] = root.resolve() == EVE_ROOT.resolve() if root.exists() else False
        row["exists"] = root.exists()
        rows.append(row)
    return rows


def set_active_installation(name: str) -> dict[str, Any]:
    clean_name = _safe_name(name)
    account = load_local_account()
    installations = account.get("installations") or []
    match = next((item for item in installations if _safe_name(item.get("name", "")) == clean_name), None)
    if not match:
        raise ValueError(f"installation profile not found: {name}")
    account["active_installation"] = clean_name
    save_local_account(account)
    root = Path(str(match.get("root") or ""))
    return {
        "ok": True,
        "active_installation": clean_name,
        "root": str(root),
        "matches_current_root": root.exists() and root.resolve() == EVE_ROOT.resolve(),
        "current_root": str(EVE_ROOT),
    }


def active_installation() -> dict[str, Any]:
    account = load_local_account()
    active = str(account.get("active_installation") or "")
    for item in list_installations():
        if _safe_name(item.get("name", "")) == active:
            return item
    return {
        "name": "",
        "label": "",
        "root": str(EVE_ROOT),
        "active": False,
        "current_root": True,
        "exists": EVE_ROOT.exists(),
    }


def ensure_default_installation(name: str = "local", root: str | Path = EVE_ROOT) -> dict[str, Any]:
    if not any(_safe_name(item.get("name", "")) == _safe_name(name) for item in list_installations()):
        return upsert_installation(name, root, make_active=True)
    return {"ok": True, "changed": False}


def configure_account(access_code: str | None, install_name: str, install_root: str | Path, *, add_sandro_defaults: bool = False) -> dict[str, Any]:
    if access_code:
        set_access_code(access_code, overwrite=not bool(load_local_account().get("access_code")))
    upsert_installation(install_name, install_root, make_active=True)
    if add_sandro_defaults:
        upsert_installation("pc1", r"D:\Eve", make_active=False)
        upsert_installation("pc2", r"E:\eve", make_active=False)
    return {
        "ok": True,
        "account_path": str(ACCOUNT_PATH),
        "installations": list_installations(),
        "active_installation": active_installation(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure Eve local account and installation profiles")
    sub = parser.add_subparsers(dest="cmd", required=True)
    cfg = sub.add_parser("configure")
    cfg.add_argument("--access-code", default="")
    cfg.add_argument("--install-name", default="local")
    cfg.add_argument("--install-root", default=str(EVE_ROOT))
    cfg.add_argument("--add-sandro-defaults", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args()
    if args.cmd == "configure":
        print(json.dumps(configure_account(args.access_code, args.install_name, args.install_root, add_sandro_defaults=args.add_sandro_defaults), indent=2, ensure_ascii=False))
        return 0
    if args.cmd == "status":
        print(json.dumps({"account_path": str(ACCOUNT_PATH), "installations": list_installations(), "active_installation": active_installation()}, indent=2, ensure_ascii=False))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
