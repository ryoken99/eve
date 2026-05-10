from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import SKILLS_DIR, ensure_project_dirs
from security.audit_log import log_event
from tools.filesystem import append_file, read_file, write_file
from tools.terminal import run_command
from tools.browser_human import open_url, search_web
from tools.email_human import create_gmail_draft
from tools.web_research import run_web_research_report
from tools.x_human import publish_current_x_composer
from computer.visual_executor import click_text_and_verify
from computer.vision import find_text_on_screen
from security.permission_manager import check_action


def _list_arg(value):
    if value is None or isinstance(value, list):
        return value
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _bool_arg(value, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"0", "false", "no", "nao", "não", "off"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def create_draft_skill(name: str, description: str, steps: list[dict], permissions: list[str] | None = None) -> Path:
    ensure_project_dirs()
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.strip().lower())
    path = SKILLS_DIR / "draft" / f"{safe_name}.json"
    payload = {
        "name": safe_name,
        "description": description,
        "risk_level": "low",
        "permissions": permissions or [],
        "steps": steps,
        "success_check": [],
        "version": 1,
        "status": "draft",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def list_skills(status: str | None = None) -> list[str]:
    ensure_project_dirs()
    roots = [SKILLS_DIR / status] if status else [p for p in SKILLS_DIR.iterdir() if p.is_dir()]
    found = []
    for root in roots:
        for path in root.rglob("*.json"):
            found.append(str(path.relative_to(SKILLS_DIR).with_suffix("")).replace("\\", "/"))
    return sorted(found)


def load_skill(skill_ref: str) -> dict:
    ensure_project_dirs()
    if "/" in skill_ref:
        path = SKILLS_DIR / f"{skill_ref}.json"
    else:
        candidates = list(SKILLS_DIR.glob(f"*/{skill_ref}.json"))
        if not candidates:
            raise FileNotFoundError(f"Skill nao encontrada: {skill_ref}")
        path = candidates[0]
    return json.loads(path.read_text(encoding="utf-8"))


def run_skill(skill_ref: str, *, args: dict | None = None, approved: bool = False) -> dict:
    args = args or {}
    skill = load_skill(skill_ref)
    if "publish_online" in (skill.get("permissions") or []):
        decision = check_action("publish_online", approved=approved)
        if not decision.allowed:
            raise PermissionError(decision.reason)
    results = []
    for step in skill.get("steps") or []:
        action = step.get("action")
        if action == "write_file":
            path = args.get("path") or step.get("path")
            content = args.get("content") or step.get("content", "")
            if not path:
                raise ValueError("write_file skill step precisa de path")
            results.append({"action": action, "path": str(write_file(path, content))})
        elif action == "append_file":
            path = args.get("path") or step.get("path")
            content = args.get("content") or step.get("content", "")
            if not path:
                raise ValueError("append_file skill step precisa de path")
            results.append({"action": action, "path": str(append_file(path, content))})
        elif action == "read_file":
            path = args.get("path") or step.get("path")
            if not path:
                raise ValueError("read_file skill step precisa de path")
            results.append({"action": action, "path": path, "content": read_file(path)})
        elif action == "run_command":
            command = args.get("command") or step.get("command")
            if not command:
                raise ValueError("run_command skill step precisa de command")
            results.append({"action": action, "result": run_command(command, approved=approved)})
        elif action == "browser_open_url":
            url = args.get("url") or step.get("url")
            if not url:
                raise ValueError("browser_open_url skill step precisa de url")
            results.append({"action": action, "result": open_url(url)})
        elif action == "browser_search_web":
            query = args.get("query") or step.get("query")
            if not query:
                raise ValueError("browser_search_web skill step precisa de query")
            results.append({"action": action, "result": search_web(query)})
        elif action == "web_research_report":
            query = args.get("query") or step.get("query")
            if not query:
                raise ValueError("web_research_report precisa de query")
            results.append(
                {
                    "action": action,
                    "result": run_web_research_report(
                        query,
                        seed_urls=_list_arg(args.get("seed_urls") or step.get("seed_urls")),
                        allowed_domains=_list_arg(args.get("allowed_domains") or step.get("allowed_domains")),
                        max_pages=int(args.get("max_pages") or step.get("max_pages") or 8),
                        open_visible_browser=_bool_arg(
                            args.get("open_visible_browser", step.get("open_visible_browser")),
                            default=True,
                        ),
                    ),
                }
            )
        elif action == "gmail_create_draft":
            to = args.get("to") or step.get("to")
            subject = args.get("subject") or step.get("subject")
            body = args.get("body") or step.get("body")
            if not to or not subject or not body:
                raise ValueError("gmail_create_draft precisa de to, subject e body")
            results.append({"action": action, "result": create_gmail_draft(to, subject, body)})
        elif action == "verify_text":
            text = args.get("text") or step.get("text")
            if not text:
                raise ValueError("verify_text precisa de text")
            results.append({"action": action, "result": find_text_on_screen(text)})
        elif action == "click_text":
            text = args.get("click_text") or step.get("text")
            verify_text = args.get("verify_text") or step.get("verify_text")
            if not text:
                raise ValueError("click_text precisa de text")
            results.append({"action": action, "result": click_text_and_verify(text, verify_text)})
        elif action == "verify_text_absent_or_feed":
            text = args.get("text") or step.get("text")
            if not text:
                raise ValueError("verify_text_absent_or_feed precisa de text")
            found = find_text_on_screen(text)
            found["status"] = "informational"
            found["note"] = "Informational OCR sample only; x_publish_current_composer owns the publish success/failure decision."
            results.append({"action": action, "result": found})
        elif action == "x_publish_current_composer":
            text = args.get("text") or step.get("text")
            if not text:
                raise ValueError("x_publish_current_composer precisa de text")
            results.append({"action": action, "result": publish_current_x_composer(text, approved=approved)})
        else:
            raise ValueError(f"Acao de skill desconhecida: {action}")
    failed_steps = []
    failure_statuses = {
        "failed",
        "failed_tests",
        "partial",
        "needs_confirmation",
        "needs_review",
        "needs_human_review",
        "blocked",
        "text_too_long",
        "composer_not_verified",
        "post_button_not_found",
    }
    for index, item in enumerate(results, start=1):
        result = item.get("result") if isinstance(item, dict) else None
        if not isinstance(result, dict):
            continue
        status = result.get("status")
        verification = result.get("verification")
        verification_failed = isinstance(verification, dict) and not verification.get("ok", True)
        if status in failure_statuses or verification_failed:
            failed_steps.append(
                {
                    "index": index,
                    "action": item.get("action"),
                    "status": status or "verification_failed",
                    "reason": (verification or {}).get("reason") if isinstance(verification, dict) else None,
                }
            )
    payload = {
        "skill": skill.get("name"),
        "skill_status": skill.get("status"),
        "status": "failed" if failed_steps else "completed",
        "results": results,
        "verification": {
            "ok": not failed_steps,
            "rule": "all_skill_steps_verified",
            "failed_steps": failed_steps,
        },
    }
    log_event("skill_executed", payload)
    return payload


def promote_skill(name: str) -> Path:
    source = SKILLS_DIR / "draft" / f"{name}.json"
    if not source.exists():
        raise FileNotFoundError(f"Draft skill nao encontrada: {name}")
    skill = json.loads(source.read_text(encoding="utf-8"))
    skill["status"] = "trusted"
    skill["updated_at"] = now_iso()
    dest = SKILLS_DIR / "trusted" / f"{name}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(skill, indent=2, ensure_ascii=False), encoding="utf-8")
    source.unlink()
    log_event("skill_promoted", {"name": name, "dest": str(dest)})
    return dest
