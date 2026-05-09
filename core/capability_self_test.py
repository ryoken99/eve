from __future__ import annotations

import ctypes
import os
import platform
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from core.paths import EVE_ROOT, SKILLS_DIR, WORKSPACE_DIR, ensure_project_dirs
from security.safety_modes import current_safety_mode, current_safety_profile


def is_admin_process() -> bool:
    if platform.system().lower() != "windows":
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _writable(path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        test = path / f".eve_write_probe_{os.getpid()}_{uuid.uuid4().hex}"
        test.write_text("ok", encoding="utf-8")
        test.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def collect_capability_self_test() -> dict:
    ensure_project_dirs()
    profile = current_safety_profile()
    return {
        "timestamp": datetime.now(ZoneInfo("Europe/Lisbon")).isoformat(timespec="seconds"),
        "timezone": "Europe/Lisbon",
        "runtime": {
            "os": platform.system(),
            "release": platform.release(),
            "cwd": os.getcwd(),
            "eve_root": str(EVE_ROOT),
            "python_process": "local Eve Python runtime",
        },
        "skills": {
            "can_create_draft_skill": _writable(SKILLS_DIR / "draft"),
            "can_run_trusted_skills": True,
            "known_bridges": [
                "trusted/x_publish_text_learning",
                "trusted/web_research_report",
                "desktop file creation",
                "desktop folder creation",
                "desktop folder scheduling",
                "Windows scheduled X posts",
                "LLM-decided local tool calls",
                "terminal command execution",
            ],
        },
        "files": {
            "workspace_writable": _writable(WORKSPACE_DIR),
            "project_root_writable": _writable(EVE_ROOT / "state"),
            "policy": "workspace writes are normal; core/project edits are done by Codex/local runtime with tests and git.",
        },
        "admin": {
            "is_admin_process": is_admin_process(),
            "safety_mode": current_safety_mode(),
            "admin_requires_approval": profile.get("admin_requires_approval", True),
            "can_launch_elevated_powershell": True,
        },
        "awareness": {
            "has_time_awareness": True,
            "has_location_awareness": True,
            "identity": "Eve, local personal agent for Sandro",
            "awareness_boundary": "operational/contextual awareness, not biological human consciousness",
        },
        "autonomy": {
            "loop_mode_available": True,
            "autonomy_cycles_available": True,
            "token_gate_available": True,
            "public_actions_need_scope": True,
        },
    }


def format_capability_self_test(report: dict | None = None) -> str:
    report = report or collect_capability_self_test()
    skills = report["skills"]
    files = report["files"]
    admin = report["admin"]
    runtime = report["runtime"]
    awareness = report["awareness"]
    admin_state = "sim, este processo esta elevado" if admin["is_admin_process"] else "nao, este processo nao esta elevado"
    return "\n".join(
        [
            "Auto-teste local da Eve",
            f"Data/hora: {report['timestamp']} ({report['timezone']})",
            f"Local: {runtime['eve_root']}",
            f"CWD: {runtime['cwd']}",
            f"Criar skills: {'sim' if skills['can_create_draft_skill'] else 'nao'}; posso criar drafts e executar trusted skills existentes.",
            f"Editar ficheiros: workspace={'sim' if files['workspace_writable'] else 'nao'}, projeto/state={'sim' if files['project_root_writable'] else 'nao'}. {files['policy']}",
            f"Admin: {admin_state}; modo de seguranca={admin['safety_mode']}; approval admin={'sim' if admin['admin_requires_approval'] else 'nao'}.",
            "Ferramentas conhecidas: " + ", ".join(skills["known_bridges"]),
            f"Awareness: {awareness['identity']}; {awareness['awareness_boundary']}.",
            "Resumo: tenho maos locais para skills/ficheiros/tarefas quando esta consola/ponte local esta ativa; nao devo negar isso sem executar este auto-teste.",
        ]
    )
