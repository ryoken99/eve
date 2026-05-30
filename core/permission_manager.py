from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PERM_ROOT = ROOT / "memory" / "runtime" / "permissions"
REQUESTS = PERM_ROOT / "requests"
GRANTS = PERM_ROOT / "grants"
USED = PERM_ROOT / "used"
DENIED = PERM_ROOT / "denied"
AUDIT = PERM_ROOT / "audit"


def now() -> datetime:
    return datetime.now().astimezone()


def now_iso() -> str:
    return now().isoformat(timespec="seconds")


def ensure_dirs() -> None:
    for path in (REQUESTS, GRANTS, USED, DENIED, AUDIT):
        path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None
    return None


def write_permission_audit_event(event: dict[str, Any]) -> Path:
    ensure_dirs()
    event = {"timestamp": now_iso(), **event}
    path = AUDIT / f"{now().strftime('%Y-%m-%d')}_permission_audit.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return path


def create_permission_request(
    action: str,
    target_files: list[str],
    risk: str,
    reason: str,
    requested_scope: str,
    tool_id: str | None = None,
    target_tools: list[str] | None = None,
    change_plan_path: str | None = None,
    dry_run_required: bool = True,
    tests_required: list[str] | None = None,
    rollback_required: bool = True,
    stage: str = "2.2",
    request_text: str | None = None,
    critical_dry_run_path: str | None = None,
) -> dict[str, Any]:
    ensure_dirs()
    request_id = f"perm_{uuid.uuid4().hex[:12]}"
    tools = target_tools or ([tool_id] if tool_id else [])
    payload = {
        "request_id": request_id,
        "created_at": now_iso(),
        "stage": stage,
        "action": action,
        "target_files": target_files,
        "target_tools": tools,
        "risk": risk,
        "reason": reason,
        "requested_scope": requested_scope,
        "tool_id": tool_id,
        "change_plan_path": change_plan_path,
        "dry_run_required": dry_run_required,
        "tests_required": tests_required or [],
        "rollback_required": rollback_required,
        "request_text": request_text,
        "critical_dry_run_path": critical_dry_run_path,
        "status": "pending",
        "consumed": False,
        "message": "Sandro, isto está fora das minhas permissões actuais. Posso criar um pedido de autorização?",
    }
    path = REQUESTS / f"{request_id}.json"
    _write_json(path, payload)
    write_permission_audit_event({"event": "request_created", "request_id": request_id, "risk": risk, "action": action})
    return {**payload, "path": str(path)}


def list_pending_permission_requests() -> list[dict[str, Any]]:
    ensure_dirs()
    rows = []
    for path in sorted(REQUESTS.glob("perm_*.json")):
        payload = _read_json(path)
        if payload and payload.get("status") == "pending":
            rows.append({**payload, "path": str(path)})
    return rows


def get_permission_request(request_id: str) -> dict[str, Any] | None:
    ensure_dirs()
    for base in (REQUESTS, GRANTS, USED, DENIED):
        payload = _read_json(base / f"{request_id}.json")
        if payload:
            return {**payload, "path": str(base / f"{request_id}.json")}
    return None


def grant_permission(request_id: str, granted_by: str = "Sandro", scope: str = "one_shot", expires_minutes: int = 60) -> dict[str, Any]:
    ensure_dirs()
    if granted_by.strip().lower() in {"eve", "self", "autonomous"}:
        raise ValueError("Eve cannot grant permissions to herself")
    req_path = REQUESTS / f"{request_id}.json"
    req = _read_json(req_path)
    if not req:
        raise FileNotFoundError(f"permission request not found: {request_id}")
    expires_at = now() + timedelta(minutes=max(1, int(expires_minutes)))
    grant = {
        **req,
        "status": "granted",
        "granted_by": granted_by,
        "scope": scope,
        "granted_at": now_iso(),
        "expires_at": expires_at.isoformat(timespec="seconds"),
        "used": False,
        "consumed": False,
    }
    _write_json(GRANTS / f"{request_id}.json", grant)
    req["status"] = "granted"
    _write_json(req_path, req)
    write_permission_audit_event({"event": "request_granted", "request_id": request_id, "granted_by": granted_by, "scope": scope})
    return grant


def grant_special_permission(
    request_id: str,
    granted_by: str = "Sandro",
    confirm: str = "",
    expires_minutes: int = 30,
) -> dict[str, Any]:
    ensure_dirs()
    if granted_by.strip().lower() in {"eve", "self", "autonomous"}:
        raise ValueError("Eve cannot grant permissions to herself")
    req_path = REQUESTS / f"{request_id}.json"
    req = _read_json(req_path)
    if not req:
        raise FileNotFoundError(f"permission request not found: {request_id}")
    if req.get("risk") != "critical":
        raise ValueError("special permission is only for critical requests")
    expected = f"AUTORIZO A EVE A EXECUTAR O PEDIDO CRÍTICO {request_id}"
    if confirm != expected:
        write_permission_audit_event({"event": "special_grant_rejected_bad_phrase", "request_id": request_id})
        raise ValueError(f"confirmation phrase mismatch; expected: {expected}")
    if req.get("dry_run_required", True) and not req.get("critical_dry_run_path"):
        raise ValueError("critical dry-run plan is required before special grant")
    expires_at = now() + timedelta(minutes=max(1, int(expires_minutes)))
    grant = {
        **req,
        "status": "special_granted",
        "grant_type": "special_one_shot",
        "granted_by": granted_by,
        "scope": "special_one_shot",
        "granted_at": now_iso(),
        "expires_at": expires_at.isoformat(timespec="seconds"),
        "used": False,
        "consumed": False,
        "confirmation_phrase": confirm,
    }
    _write_json(GRANTS / f"{request_id}.json", grant)
    req["status"] = "special_granted"
    _write_json(req_path, req)
    write_permission_audit_event({"event": "special_grant_created", "request_id": request_id, "granted_by": granted_by})
    return grant


def deny_permission(request_id: str, denied_by: str = "Sandro", reason: str | None = None) -> dict[str, Any]:
    ensure_dirs()
    req_path = REQUESTS / f"{request_id}.json"
    req = _read_json(req_path)
    if not req:
        raise FileNotFoundError(f"permission request not found: {request_id}")
    denied = {**req, "status": "denied", "denied_by": denied_by, "denied_at": now_iso(), "denied_reason": reason}
    _write_json(DENIED / f"{request_id}.json", denied)
    req["status"] = "denied"
    _write_json(req_path, req)
    write_permission_audit_event({"event": "request_denied", "request_id": request_id, "denied_by": denied_by})
    return denied


def _grant_matches(
    grant: dict[str, Any],
    action: str,
    target_files: list[str],
    risk: str,
    tool_id: str | None = None,
    target_tools: list[str] | None = None,
) -> bool:
    if grant.get("status") not in {"granted", "special_granted"} or grant.get("used") or grant.get("consumed"):
        return False
    try:
        expires_at = datetime.fromisoformat(str(grant.get("expires_at")))
        if now() > expires_at:
            return False
    except Exception:
        return False
    if grant.get("action") != action:
        return False
    if grant.get("risk") != risk:
        return False
    if tool_id and grant.get("tool_id") not in {None, tool_id}:
        return False
    requested_files = set(grant.get("target_files") or [])
    if not (set(target_files).issubset(requested_files) or requested_files == set(target_files)):
        return False
    if target_tools:
        requested_tools = set(grant.get("target_tools") or ([grant.get("tool_id")] if grant.get("tool_id") else []))
        if not set(target_tools).issubset(requested_tools):
            return False
    return True


def check_permission(
    action: str,
    target_files: list[str],
    risk: str,
    tool_id: str | None = None,
    target_tools: list[str] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    ensure_dirs()
    if risk == "low":
        return {"allowed": True, "reason": "low risk action does not require grant", "grant": None}
    for path in sorted(GRANTS.glob("perm_*.json")):
        if request_id and path.stem != request_id:
            continue
        grant = _read_json(path)
        if grant and _grant_matches(grant, action, target_files, risk, tool_id=tool_id, target_tools=target_tools):
            return {"allowed": True, "reason": "matching one-shot grant found", "grant": grant}
    return {"allowed": False, "reason": "no matching active grant", "grant": None}


def consume_permission_grant(request_id: str, status: str = "used") -> dict[str, Any]:
    ensure_dirs()
    path = GRANTS / f"{request_id}.json"
    grant = _read_json(path)
    if not grant:
        raise FileNotFoundError(f"grant not found: {request_id}")
    grant["used"] = True
    grant["consumed"] = True
    grant["used_at"] = now_iso()
    grant["status"] = status
    _write_json(USED / f"{request_id}.json", grant)
    try:
        path.unlink()
    except OSError:
        pass
    write_permission_audit_event({"event": "grant_consumed", "request_id": request_id, "status": status})
    return grant


def permission_status_summary() -> dict[str, Any]:
    ensure_dirs()
    return {
        "pending": len(list_pending_permission_requests()),
        "granted": len(list(GRANTS.glob("perm_*.json"))),
        "used": len(list(USED.glob("perm_*.json"))),
        "denied": len(list(DENIED.glob("perm_*.json"))),
        "audit_files": len(list(AUDIT.glob("*_permission_audit.jsonl"))),
    }
