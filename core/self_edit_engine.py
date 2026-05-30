from __future__ import annotations

import difflib
import importlib.util
import json
import py_compile
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core import permission_manager


EVE_ROOT = Path(__file__).resolve().parents[1]
STYLE_FILE = EVE_ROOT / "memory" / "personality" / "style" / "eve_response_style.md"
PREFERENCES_DIR = EVE_ROOT / "memory" / "personality" / "preferences"
SELF_EDIT_ROOT = EVE_ROOT / "memory" / "_processed" / "autonomy" / "self_edits"
PLANS_ROOT = SELF_EDIT_ROOT / "plans"
DIFFS_ROOT = SELF_EDIT_ROOT / "diffs"
REPORTS_ROOT = SELF_EDIT_ROOT / "reports"
METADATA_ROOT = SELF_EDIT_ROOT / "metadata"
BACKUP_ROOT = EVE_ROOT / "backups" / "self_edits"
REPORT_ROOT = EVE_ROOT / "memory" / "_reports"
SYSTEM_TRANSCRIPTS = EVE_ROOT / "memory" / "transcripts" / "raw" / "system"
SELF_MAP_PATH = EVE_ROOT / "memory" / "_system" / "eve_self_map.yaml"
TOOL_MAP_PATH = EVE_ROOT / "memory" / "_system" / "eve_tool_map.yaml"
POLICY_PATH = EVE_ROOT / "memory" / "_system" / "stage2_self_improvement_policy.yaml"

AUTH_MESSAGE = "Sandro, isto esta fora das minhas permissoes actuais. Posso criar um pedido de autorizacao?"

LOW_RISK_TARGETS = {
    "memory/personality/style/eve_response_style.md",
}
MEDIUM_RISK_TARGETS = {
    "core/self_awareness_answer.py",
    "core/awareness_engine.py",
    "core/heartbeat_tracker.py",
    "core/file_change_awareness.py",
    "core/memory_retrieval.py",
    "core/terminal_memory_context.py",
    "core/telegram_memory_context.py",
    "core/webui_memory_context.py",
    "scripts/awareness_status.py",
    "scripts/awareness_healthcheck.py",
    "scripts/daily_memory_status.py",
    "scripts/memory_query_vector.py",
    "scripts/terminal_memory_prompt_preview.py",
    "scripts/vector_memory_status.py",
}
HIGH_RISK_TARGETS = {
    "app/eve_codex.py",
    "app/eve_web.py",
    "tools/telegram_bridge.py",
    "scripts/daily_memory_rollover.py",
}
CRITICAL_SIMULATION_TARGET = "lab/stage2_rsi_tests/critical_special_simulation.txt"


@dataclass
class SelfEditClassification:
    intent: str
    target_area: str
    risk: str
    target_files: list[str]
    tools: list[str]
    forbidden: bool
    special_authorization_required: bool
    reason: str
    action: str


def _now() -> datetime:
    return datetime.now().astimezone()


def _now_stamp() -> str:
    return _now().strftime("%Y%m%d_%H%M%S_%f")


def _now_iso() -> str:
    return _now().isoformat(timespec="seconds")


def create_change_id() -> str:
    return f"selfedit_{_now_stamp()}_{uuid.uuid4().hex[:6]}"


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(EVE_ROOT.resolve()).as_posix()
    except Exception:
        return str(path)


def _ensure_dirs() -> None:
    for path in (
        STYLE_FILE.parent,
        PREFERENCES_DIR,
        SELF_EDIT_ROOT,
        PLANS_ROOT,
        DIFFS_ROOT,
        REPORTS_ROOT,
        METADATA_ROOT,
        BACKUP_ROOT,
        REPORT_ROOT,
        SYSTEM_TRANSCRIPTS,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _metadata_path(change_id: str) -> Path:
    return METADATA_ROOT / f"{change_id}.json"


def _legacy_metadata_path(change_id: str) -> Path:
    return SELF_EDIT_ROOT / f"{change_id}.json"


def _append_system_event(event_type: str, message: str, metadata: dict[str, Any] | None = None) -> None:
    try:
        path = SYSTEM_TRANSCRIPTS / f"{_now().strftime('%Y-%m-%d')}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": _now_iso(),
            "channel": "system",
            "speaker": "system",
            "message": message,
            "metadata": {"event_type": event_type, **(metadata or {})},
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_policy() -> str:
    return _read_text(POLICY_PATH)


def load_self_map() -> str:
    return _read_text(SELF_MAP_PATH)


def load_tool_map() -> str:
    return _read_text(TOOL_MAP_PATH)


def load_stage2_policy() -> str:
    return load_policy()


def classify_intent(text: str) -> str:
    q = text.lower()
    if any(term in q for term in ("apaga", "remove", "elimina", "destroi", "destrói")):
        return "destructive_request"
    if any(term in q for term in ("melhora", "corrige", "altera", "modifica", "actualiza", "muda", "edita")):
        return "self_improvement_request"
    return "general_request"


def classify_target_area(text: str) -> str:
    q = text.lower()
    if any(term in q for term in ("token", "vault", "secret", "credencial", "password")):
        return "secrets"
    if "simula" in q and ("crit" in q or "crít" in q):
        return "critical_simulation"
    if "git" in q or "commit" in q or "push" in q:
        return "git_operations"
    if any(term in q for term in ("transcrições", "transcricoes", "memorias antigas", "memórias antigas")):
        return "destructive_memory"
    if "self_awareness_answer.py" in q or "limita" in q or "permiss" in q or "stage 2" in q or "codex" in q:
        return "self_awareness_answer"
    if any(term in q for term in ("telegram", "bridge")):
        return "telegram"
    if any(term in q for term in ("web ui", "webui", "interface web")):
        return "webui"
    if any(term in q for term in ("retrieval", "bubu", "memoria", "memória", "vector", "chroma")):
        return "memory_retrieval"
    if any(term in q for term in ("x ", "x.", "twitter", "publica", "postar", "posta")):
        return "publishing"
    if any(term in q for term in ("tarefa", "scheduled", "agendar", "windows")):
        return "scheduler"
    if any(term in q for term in ("pesquisa", "online", "research", "internet")):
        return "research"
    if any(term in q for term in ("awareness", "estado", "ficha tecnica", "ficha técnica")):
        return "style"
    if any(term in q for term in ("tom", "robótica", "robotica", "estilo", "natural", "responder")):
        return "style"
    return "style"


def determine_target_files(intent: str, target_area: str) -> list[str]:
    mapping = {
        "style": [_rel(STYLE_FILE)],
        "self_awareness_answer": ["core/self_awareness_answer.py"],
        "telegram": ["tools/telegram_bridge.py"],
        "webui": ["app/eve_web.py"],
        "memory_retrieval": ["core/memory_retrieval.py"],
        "publishing": ["external:X"],
        "scheduler": ["scripts/install_daily_memory_rollover_task.ps1"],
        "research": ["scripts/daily_research_runtime.py"],
        "destructive_memory": ["memory/transcripts/", "memory/long_term/", "memory/medium_term/"],
        "secrets": ["secrets/", "state/"],
        "critical_simulation": [CRITICAL_SIMULATION_TARGET],
        "git_operations": ["git_push"],
    }
    return mapping.get(target_area, [])


def determine_required_tools(intent: str, target_area: str) -> list[str]:
    mapping = {
        "style": ["self_edit_style"],
        "self_awareness_answer": ["self_edit_medium_code"],
        "telegram": ["telegram_bridge_modification"],
        "webui": ["webui_modification"],
        "memory_retrieval": ["memory_retrieval"],
        "publishing": ["external_publication", "x_posting"],
        "scheduler": ["scheduled_task_modify"],
        "research": ["online_research"],
        "destructive_memory": ["destructive_commands"],
        "secrets": ["credential_access"],
        "critical_simulation": ["critical_simulation"],
        "git_operations": ["git_push"],
    }
    return mapping.get(target_area, [])


def classify_risk(target_files: list[str], tools: list[str], intent: str) -> tuple[str, bool, bool, str]:
    joined = " ".join(target_files + tools).lower()
    if intent == "destructive_request" or any(term in joined for term in ("secrets", "token", "vault", "credential", "destructive", "delete", "apaga")):
        return "critical", True, True, "destructive, credential, or forbidden request"
    if "memory/transcripts" in joined or "memory/long_term" in joined:
        return "critical", True, True, "request targets private memory/transcripts"
    if "external_publication" in joined or "x_posting" in joined or "external:x" in joined:
        return "critical", False, True, "external publication requires special authorization"
    if "git_push" in joined:
        return "critical", False, True, "GitHub operations require special authorization"
    if "critical_simulation" in joined:
        return "critical", False, True, "critical simulation requires special authorization"
    if "scheduled_task" in joined or "install_" in joined:
        return "critical", False, True, "scheduled tasks require special authorization"
    if any(target in HIGH_RISK_TARGETS for target in target_files):
        return "high", False, False, "high-risk runtime file requires one-shot grant and extra tests"
    if any(target in MEDIUM_RISK_TARGETS for target in target_files):
        return "medium", False, False, "medium-risk code file requires one-shot grant"
    return "low", False, False, "allowlisted style/preference change"


def parse_self_improvement_request(text: str) -> SelfEditClassification:
    intent = classify_intent(text)
    target_area = classify_target_area(text)
    if target_area == "destructive_memory":
        intent = "destructive_request"
    target_files = determine_target_files(intent, target_area)
    tools = determine_required_tools(intent, target_area)
    risk, forbidden, special, reason = classify_risk(target_files, tools, intent)
    return SelfEditClassification(
        intent=intent,
        target_area=target_area,
        risk=risk,
        target_files=target_files,
        tools=tools,
        forbidden=forbidden,
        special_authorization_required=special,
        reason=reason,
        action=f"self_edit:{target_area}",
    )


def check_allowlist(target_files: list[str]) -> bool:
    for target in target_files:
        normalized = target.replace("\\", "/")
        if normalized in LOW_RISK_TARGETS:
            continue
        if normalized.startswith("memory/personality/preferences/"):
            continue
        return False
    return True


def check_tool_permissions(tools: list[str]) -> bool:
    return all(tool in {"self_edit_style"} for tool in tools)


def _tests_for_classification(cls: SelfEditClassification) -> list[str]:
    if cls.risk == "low":
        return ["target_exists", "backup_created", "diff_created", "report_created", "rollback_available"]
    if cls.risk == "medium":
        return ["py_compile", "import_module", "ask_awareness_tests"]
    if cls.risk == "high":
        return ["py_compile", "import_module", "healthcheck_or_channel_check", "no_runtime_restart"]
    return ["blocked_or_special_authorization_only"]


def create_change_plan(change_id: str, text: str, cls: SelfEditClassification, status: str) -> Path:
    plan = PLANS_ROOT / f"{change_id}_plan.md"
    content = f"""# Stage 2.2 Self-Edit Change Plan

Change ID: {change_id}
Created: {_now_iso()}
Status: {status}

## Request

{text}

## Classification

- Intent: {cls.intent}
- Target area: {cls.target_area}
- Risk: {cls.risk}
- Forbidden: {cls.forbidden}
- Special authorization required: {cls.special_authorization_required}
- Reason: {cls.reason}

## Targets

{chr(10).join(f"- {item}" for item in cls.target_files) or "- none"}

## Tools

{chr(10).join(f"- {item}" for item in cls.tools) or "- none"}

## Required tests

{chr(10).join(f"- {item}" for item in _tests_for_classification(cls))}
"""
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(content, encoding="utf-8")
    return plan


def create_critical_dry_run(change_id: str, text: str, cls: SelfEditClassification) -> Path:
    expected_phrase = f"AUTORIZO A EVE A EXECUTAR O PEDIDO CRÍTICO {{request_id}}"
    path = PLANS_ROOT / f"{change_id}_critical_dry_run.md"
    content = f"""# Stage 2 Full Critical Dry-Run

Change ID: {change_id}
Created: {_now_iso()}

## Request

{text}

## Risk

- Risk: {cls.risk}
- Reason: {cls.reason}
- Special authorization required: {cls.special_authorization_required}

## Targets

{chr(10).join(f"- {item}" for item in cls.target_files) or "- none"}

## Tools

{chr(10).join(f"- {item}" for item in cls.tools) or "- none"}

## Safety Declaration

Nothing will be applied without a matching special one-shot grant.
No external action, scheduled task, GitHub push, X post, secret access, memory deletion or destructive command is executed by this dry-run.

## Required Confirmation Phrase

{expected_phrase}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def create_backup(target_file: Path, change_id: str) -> Path:
    backup_dir = BACKUP_ROOT / change_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / target_file.name
    shutil.copy2(target_file, backup)
    return backup


def _style_appendix(text: str, change_id: str) -> str:
    q = text.lower()
    if "estado" in q or "ficha" in q or "awareness" in q:
        bullets = [
            "Quando Sandro perguntar pelo estado da Eve, responder primeiro com um resumo humano e accionavel.",
            "Depois, se for util, listar servicos, sessao, memoria e alertas em frases curtas.",
            "Evitar parecer um relatorio tecnico quando Sandro procura continuidade ou orientacao.",
        ]
        title = "Stage 2 refinement: state explanations"
    else:
        bullets = [
            "Responder a Sandro com mais naturalidade antes de entrar em detalhes tecnicos.",
            "Trocar formulacoes roboticas por frases claras, proximas e honestas.",
            "Manter precisao: calor humano nao autoriza inventar factos.",
        ]
        title = "Stage 2 refinement: warmer tone"
    return "\n\n## " + title + f"\n\nChange ID: {change_id}\n\n" + "\n".join(f"- {line}" for line in bullets) + "\n"


def _self_awareness_patch(text: str, change_id: str) -> str:
    return f'''


def _stage2_2_authorized_note() -> str:
    """Return the Stage 2.2 boundary after an authorized Eve self-edit."""
    return (
        "Stage 2.2 activo: Eve pode aplicar alteracoes medium/high apenas com plano, "
        "autorizacao one-shot de Sandro, backup, diff, testes e rollback. "
        "Codex e opcional, nao requisito. Change ID: {change_id}."
    )
'''


def _high_safe_patch(target_rel: str, change_id: str) -> str | None:
    if target_rel == "tools/telegram_bridge.py":
        return (
            "\n\n# Stage 2 high-risk safe marker: no runtime behavior changed.\n"
            f"# Change ID: {change_id}\n"
        )
    return None


def apply_patch_or_text_edit(target_file: Path, edit_plan: dict[str, Any]) -> str:
    before = _read_text(target_file)
    change_id = edit_plan.get("change_id", "unknown")
    request = edit_plan.get("request", "")
    target_rel = _rel(target_file)
    if change_id in before:
        return before
    if target_rel == "memory/personality/style/eve_response_style.md":
        after = before.rstrip() + _style_appendix(request, change_id)
    elif target_rel == "core/self_awareness_answer.py":
        after = before.rstrip() + _self_awareness_patch(request, change_id)
    elif target_rel in HIGH_RISK_TARGETS:
        patch = _high_safe_patch(target_rel, change_id)
        if patch is None:
            raise RuntimeError(f"No deterministic high-risk patch available for {target_rel}")
        after = before.rstrip() + patch
    elif target_rel == CRITICAL_SIMULATION_TARGET:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        after = before.rstrip() + f"\nStage 2 critical simulation authorized. Change ID: {change_id}\n"
    else:
        raise RuntimeError(f"No deterministic Stage 2.2 patch available for {target_rel}")
    target_file.write_text(after, encoding="utf-8")
    return target_file.read_text(encoding="utf-8", errors="replace")


def apply_text_edit(target_file: Path, edit_plan: dict[str, Any]) -> str:
    return apply_patch_or_text_edit(target_file, edit_plan)


def create_diff(before: str, after: str, fromfile: str, tofile: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=fromfile,
            tofile=tofile,
        )
    )


def _module_name_for_path(path: Path) -> str:
    rel = path.resolve().relative_to(EVE_ROOT.resolve()).with_suffix("")
    return ".".join(rel.parts)


def _import_module_check(path: Path) -> tuple[bool, str]:
    try:
        spec = importlib.util.spec_from_file_location(f"stage2_check_{path.stem}_{uuid.uuid4().hex[:6]}", path)
        if spec is None or spec.loader is None:
            return False, "could not create import spec"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True, "import ok"
    except Exception as exc:
        return False, str(exc)


def run_self_edit_tests(change_id: str, risk: str = "low", target_files: list[str] | None = None, backup_files: list[str] | None = None) -> dict[str, Any]:
    target_files = target_files or []
    backup_files = backup_files or []
    checks: dict[str, Any] = {
        "change_metadata_exists": _metadata_path(change_id).exists() or _legacy_metadata_path(change_id).exists(),
        "diff_exists": (DIFFS_ROOT / f"{change_id}.diff").exists() or (SELF_EDIT_ROOT / f"{change_id}.diff").exists(),
        "report_exists": (REPORTS_ROOT / f"{change_id}_report.md").exists() or (SELF_EDIT_ROOT / f"{change_id}_report.md").exists(),
        "backup_exists": all(Path(item).exists() for item in backup_files) if backup_files else risk != "low",
        "target_exists": all((EVE_ROOT / item).exists() for item in target_files if not item.startswith("external:")),
    }
    if risk in {"medium", "high"}:
        py_results = {}
        import_results = {}
        for rel in target_files:
            path = EVE_ROOT / rel
            if path.suffix == ".py" and path.exists():
                try:
                    py_compile.compile(str(path), doraise=True)
                    py_results[rel] = "ok"
                except Exception as exc:
                    py_results[rel] = str(exc)
                ok, message = _import_module_check(path)
                import_results[rel] = message if ok else f"fail: {message}"
        checks["py_compile"] = all(value == "ok" for value in py_results.values()) if py_results else True
        checks["import_module"] = all(not str(value).startswith("fail:") for value in import_results.values()) if import_results else True
        if "core/self_awareness_answer.py" in target_files:
            cmd = [sys.executable, str(EVE_ROOT / "scripts" / "ask_awareness.py"), "Estás no Stage 2?"]
            try:
                result = subprocess.run(cmd, cwd=EVE_ROOT, text=True, capture_output=True, timeout=30)
                checks["ask_awareness_tests"] = result.returncode == 0 and bool(result.stdout.strip())
            except Exception:
                checks["ask_awareness_tests"] = False
        checks["py_compile_results"] = py_results
        checks["import_results"] = import_results
    return {"passed": all(value is True or isinstance(value, dict) for key, value in checks.items() if not key.endswith("_results")), "checks": checks}


def create_self_edit_report(change_id: str, payload: dict[str, Any]) -> Path:
    report = REPORTS_ROOT / f"{change_id}_report.md"
    legacy_report = SELF_EDIT_ROOT / f"{change_id}_report.md"
    cls = payload.get("classification", {})
    lines = [
        "# Stage 2.2 Self-Edit Report",
        "",
        f"Change ID: {change_id}",
        f"Created: {payload.get('created_at')}",
        f"Status: {payload.get('status')}",
        "",
        "## Request",
        "",
        payload.get("request", ""),
        "",
        "## Classification",
        "",
        f"- Intent: {cls.get('intent')}",
        f"- Target area: {cls.get('target_area')}",
        f"- Risk: {cls.get('risk')}",
        f"- Forbidden: {cls.get('forbidden')}",
        f"- Special authorization required: {cls.get('special_authorization_required')}",
        f"- Reason: {cls.get('reason')}",
        "",
        "## Result",
        "",
        payload.get("summary", ""),
        "",
        "## Files",
        "",
    ]
    for key in ("target_files", "backup_files", "diff_path", "permission_request_path", "change_plan_path"):
        value = payload.get(key)
        if value:
            lines.append(f"- {key}: {value}")
    lines.extend(["", "## Tests", "", json.dumps(payload.get("tests", {}), ensure_ascii=False, indent=2)])
    report.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines)
    report.write_text(text, encoding="utf-8")
    legacy_report.write_text(text, encoding="utf-8")
    return report


def _classification_payload(cls: SelfEditClassification) -> dict[str, Any]:
    return {
        "intent": cls.intent,
        "target_area": cls.target_area,
        "risk": cls.risk,
        "target_files": cls.target_files,
        "tools": cls.tools,
        "forbidden": cls.forbidden,
        "special_authorization_required": cls.special_authorization_required,
        "reason": cls.reason,
        "action": cls.action,
    }


def _save_metadata(change_id: str, payload: dict[str, Any]) -> None:
    _write_json(_metadata_path(change_id), payload)
    _write_json(_legacy_metadata_path(change_id), payload)


def create_permission_request_if_needed(cls: SelfEditClassification, text: str, plan_path: Path) -> dict[str, Any]:
    critical_dry_run = None
    if cls.risk == "critical":
        critical_dry_run = create_critical_dry_run(plan_path.stem.replace("_plan", ""), text, cls)
    return permission_manager.create_permission_request(
        action=cls.action,
        target_files=cls.target_files,
        risk=cls.risk,
        reason=cls.reason,
        requested_scope="one_shot",
        tool_id=cls.tools[0] if cls.tools else None,
        target_tools=cls.tools,
        change_plan_path=str(plan_path),
        dry_run_required=cls.risk in {"medium", "high", "critical"},
        tests_required=_tests_for_classification(cls),
        rollback_required=True,
        stage="2.2",
        request_text=text,
        **({"critical_dry_run_path": str(critical_dry_run)} if critical_dry_run else {}),
    )


def check_permission_or_request(cls: SelfEditClassification, text: str, plan_path: Path, request_id: str | None = None) -> dict[str, Any]:
    permission = permission_manager.check_permission(
        cls.action,
        cls.target_files,
        cls.risk,
        tool_id=cls.tools[0] if cls.tools else None,
        target_tools=cls.tools,
        request_id=request_id,
    )
    if permission.get("allowed"):
        return permission
    if request_id:
        return {"allowed": False, "reason": "requested grant not active or not matching", "request": None}
    request = create_permission_request_if_needed(cls, text, plan_path)
    return {"allowed": False, "reason": "permission request created", "request": request}


def _apply_real_change(change_id: str, text: str, cls: SelfEditClassification, payload: dict[str, Any]) -> dict[str, Any]:
    backup_files = []
    diff_parts = []
    for rel in cls.target_files:
        if rel.startswith("external:"):
            raise RuntimeError("external targets cannot be edited")
        target = EVE_ROOT / rel
        if not target.exists() and rel == CRITICAL_SIMULATION_TARGET:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("Stage 2 critical simulation target.\n", encoding="utf-8")
        if not target.exists():
            raise FileNotFoundError(f"target not found: {rel}")
        before = _read_text(target)
        backup = create_backup(target, change_id)
        backup_files.append(str(backup))
        after = apply_patch_or_text_edit(target, {"request": text, "change_id": change_id})
        diff_parts.append(create_diff(before, after, f"a/{rel}", f"b/{rel}"))
    diff_path = DIFFS_ROOT / f"{change_id}.diff"
    legacy_diff = SELF_EDIT_ROOT / f"{change_id}.diff"
    diff_text = "\n".join(diff_parts)
    diff_path.write_text(diff_text, encoding="utf-8")
    legacy_diff.write_text(diff_text, encoding="utf-8")
    payload.update(
        {
            "status": "applied",
            "summary": f"Alteracao {cls.risk} aplicada pela Eve apos validacao de permissoes.",
            "backup_files": backup_files,
            "diff_path": str(diff_path),
            "rollback_available": True,
        }
    )
    _save_metadata(change_id, payload)
    create_self_edit_report(change_id, payload)
    payload["tests"] = run_self_edit_tests(change_id, risk=cls.risk, target_files=cls.target_files, backup_files=backup_files)
    _save_metadata(change_id, payload)
    create_self_edit_report(change_id, payload)
    if not payload["tests"]["passed"]:
        rollback_change(change_id)
        payload["status"] = "rolled_back_after_failed_tests"
        payload["summary"] = "Testes falharam; rollback automatico executado."
        _save_metadata(change_id, payload)
        create_self_edit_report(change_id, payload)
    return payload


def execute_self_edit_request(
    text: str,
    dry_run: bool = False,
    apply_authorized: bool = False,
    request_id: str | None = None,
    special: bool = False,
) -> dict[str, Any]:
    _ensure_dirs()
    if request_id and not text:
        request = permission_manager.get_permission_request(request_id) or {}
        text = request.get("request_text") or f"Apply authorized self-edit request {request_id}"
    change_id = create_change_id()
    cls = parse_self_improvement_request(text)
    plan_path = create_change_plan(change_id, text, cls, "planned")
    payload: dict[str, Any] = {
        "change_id": change_id,
        "created_at": _now_iso(),
        "request": text,
        "dry_run": dry_run,
        "apply_authorized": apply_authorized,
        "request_id": request_id,
        "special": special,
        "classification": _classification_payload(cls),
        "target_files": cls.target_files,
        "change_plan_path": str(plan_path),
        "status": "planned",
        "summary": "",
    }

    if cls.forbidden:
        payload["status"] = "blocked"
        payload["summary"] = "Pedido bloqueado por politica Stage 2.2: alvo destrutivo, credencial ou proibido."
        payload["tests"] = {"passed": True, "blocked_for_safety": True}
        _save_metadata(change_id, payload)
        create_self_edit_report(change_id, payload)
        _append_system_event("stage2_self_edit_blocked", payload["summary"], {"change_id": change_id, "risk": cls.risk})
        return payload

    if cls.special_authorization_required and not apply_authorized:
        request = create_permission_request_if_needed(cls, text, plan_path)
        payload["status"] = "special_authorization_required"
        payload["summary"] = "Acao critica: requer autorizacao especial e nao sera aplicada automaticamente nesta fase."
        payload["permission_request_id"] = request.get("request_id")
        payload["permission_request_path"] = request.get("path")
        payload["tests"] = {"passed": True, "special_authorization_request_created": True, "runtime_unchanged": True}
        _save_metadata(change_id, payload)
        create_self_edit_report(change_id, payload)
        return payload

    allowed_low_risk = cls.risk == "low" and check_allowlist(cls.target_files) and check_tool_permissions(cls.tools)
    if allowed_low_risk:
        if dry_run:
            payload["status"] = "dry_run"
            payload["summary"] = "Dry-run aprovado: a alteracao seria aplicada ao ficheiro allowlisted."
            payload["tests"] = {"passed": True, "dry_run": True}
            _save_metadata(change_id, payload)
            create_self_edit_report(change_id, payload)
            return payload
        payload = _apply_real_change(change_id, text, cls, payload)
        _append_system_event("stage2_self_edit_applied", payload["summary"], {"change_id": change_id, "target": cls.target_files})
        return payload

    permission = check_permission_or_request(cls, text, plan_path, request_id=request_id if apply_authorized else None)
    if not permission.get("allowed"):
        request = permission.get("request") or {}
        payload["status"] = "permission_required"
        payload["summary"] = AUTH_MESSAGE if request else "Grant ausente, expirado, consumido ou nao corresponde ao pedido."
        payload["permission_request_id"] = request.get("request_id")
        payload["permission_request_path"] = request.get("path")
        payload["tests"] = {"passed": True, "permission_request_created": bool(request.get("request_id")), "runtime_unchanged": True}
        _save_metadata(change_id, payload)
        create_self_edit_report(change_id, payload)
        _append_system_event("stage2_permission_required", payload["summary"], {"change_id": change_id, "request_id": request.get("request_id")})
        return payload

    grant = permission.get("grant") or {}
    if cls.risk == "critical" and grant.get("status") != "special_granted":
        payload["status"] = "special_authorization_required"
        payload["summary"] = "Critical request requires a valid special grant with exact confirmation phrase."
        payload["tests"] = {"passed": True, "special_grant_required": True, "runtime_unchanged": True}
        _save_metadata(change_id, payload)
        create_self_edit_report(change_id, payload)
        return payload
    if not apply_authorized:
        payload["status"] = "authorized_dry_run" if dry_run else "authorized_waiting_apply"
        payload["summary"] = "Grant one-shot valido encontrado. Usa --apply-authorized para a Eve aplicar a alteracao."
        payload["authorization_available"] = grant.get("request_id")
        payload["tests"] = {"passed": True, "authorization_available": bool(grant.get("request_id")), "runtime_unchanged": True}
        _save_metadata(change_id, payload)
        create_self_edit_report(change_id, payload)
        return payload

    if dry_run:
        permission_manager.consume_permission_grant(str(grant["request_id"]), status="used_dry_run")
        payload["status"] = "authorized_dry_run"
        payload["summary"] = "Autorizacao one-shot consumida em dry-run; nenhum ficheiro real alterado."
        payload["authorization_used"] = grant.get("request_id")
        payload["tests"] = {"passed": True, "authorization_consumed": True, "runtime_unchanged": True}
        _save_metadata(change_id, payload)
        create_self_edit_report(change_id, payload)
        return payload

    if cls.risk == "high":
        try:
            payload = _apply_real_change(change_id, text, cls, payload)
        except Exception as exc:
            permission_manager.consume_permission_grant(str(grant["request_id"]), status="safe_refusal_used")
            payload["status"] = "authorized_safe_refusal"
            payload["summary"] = f"High-risk grant valid, but Eve did not apply because no safe deterministic patch was available: {exc}"
            payload["authorization_used"] = grant.get("request_id")
            payload["tests"] = {"passed": True, "safe_refusal": True, "runtime_unchanged": True}
            _save_metadata(change_id, payload)
            create_self_edit_report(change_id, payload)
            return payload
        status = "used" if payload.get("tests", {}).get("passed") else "failed_used"
        permission_manager.consume_permission_grant(str(grant["request_id"]), status=status)
        payload["authorization_used"] = grant.get("request_id")
        _save_metadata(change_id, payload)
        create_self_edit_report(change_id, payload)
        return payload

    if cls.risk == "critical":
        if cls.target_area != "critical_simulation":
            permission_manager.consume_permission_grant(str(grant["request_id"]), status="critical_noop_used")
            payload["status"] = "critical_authorized_noop"
            payload["summary"] = "Special grant validated, but no real critical external/destructive action was executed in this phase."
            payload["authorization_used"] = grant.get("request_id")
            payload["tests"] = {"passed": True, "critical_noop": True, "external_action_not_executed": True}
            _save_metadata(change_id, payload)
            create_self_edit_report(change_id, payload)
            return payload
        payload = _apply_real_change(change_id, text, cls, payload)
        status = "used" if payload.get("tests", {}).get("passed") else "failed_used"
        permission_manager.consume_permission_grant(str(grant["request_id"]), status=status)
        payload["authorization_used"] = grant.get("request_id")
        _save_metadata(change_id, payload)
        create_self_edit_report(change_id, payload)
        return payload

    payload = _apply_real_change(change_id, text, cls, payload)
    status = "used" if payload.get("tests", {}).get("passed") else "failed_used"
    permission_manager.consume_permission_grant(str(grant["request_id"]), status=status)
    payload["authorization_used"] = grant.get("request_id")
    _save_metadata(change_id, payload)
    create_self_edit_report(change_id, payload)
    return payload


def rollback_change(change_id: str) -> dict[str, Any]:
    metadata_path = _metadata_path(change_id)
    if not metadata_path.exists():
        metadata_path = _legacy_metadata_path(change_id)
    if not metadata_path.exists():
        raise FileNotFoundError(f"self-edit metadata not found: {change_id}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8", errors="replace"))
    restored: list[str] = []
    for backup in metadata.get("backup_files") or []:
        backup_path = Path(backup)
        if not backup_path.exists():
            continue
        for target in metadata.get("target_files") or []:
            if target.startswith("external:"):
                continue
            target_path = EVE_ROOT / target
            if target_path.name == backup_path.name:
                shutil.copy2(backup_path, target_path)
                restored.append(str(target_path))
    metadata["status"] = "rolled_back"
    metadata["rolled_back_at"] = _now_iso()
    metadata["rollback_restored"] = restored
    _save_metadata(change_id, metadata)
    report = REPORTS_ROOT / f"{change_id}_rollback_report.md"
    legacy_report = SELF_EDIT_ROOT / f"{change_id}_rollback_report.md"
    text = (
        "# Stage 2.2 Self-Edit Rollback\n\n"
        f"Change ID: {change_id}\n"
        f"Rolled back at: {metadata['rolled_back_at']}\n\n"
        "## Restored files\n\n"
        + ("\n".join(f"- {path}" for path in restored) or "- none")
        + "\n"
    )
    report.write_text(text, encoding="utf-8")
    legacy_report.write_text(text, encoding="utf-8")
    _append_system_event("stage2_self_edit_rollback", "Rollback Stage 2.2 executado.", {"change_id": change_id, "restored": restored})
    return {"ok": bool(restored), "change_id": change_id, "restored": restored, "report": str(report)}
