from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from security.safety_modes import current_safety_mode, current_safety_profile


READONLY_TOOLS = {
    "capability_self_test",
    "workspace_list_dir",
    "workspace_read_file",
    "describe_screen",
    "monitors",
    "screenshot_monitor",
    "ocr_status",
    "find_text_on_screen",
    "first_text_center",
    "mouse_position",
    "awareness",
    "read_diary",
    "memory_read",
    "memory_context",
    "windows_list_tasks",
    "safety_status",
    "session_search",
    "session_export",
    "plugin_summary",
    "tool_policy",
    "cron_list",
    "list_processes",
    "list_subagents",
    "vector_prefetch",
    "secrets_list",
    "secrets_get",
    "secrets_mask",
    "diagnostics_export",
    "triggers_discover",
    "context_status",
    "session_resume",
    "internal_plan",
}
SEARCH_TOOLS = {"search_web", "web_research_report", "browser_fetch_url"}
EXEC_TOOLS = {"run_terminal", "start_process", "stop_process", "poll_process", "spawn_subagent"}
PUBLIC_TOOLS = {"schedule_x_post", "publish_x_post_now", "create_gmail_draft", "gmail_search"}
MUTATING_TOOLS = {
    "create_desktop_file",
    "create_desktop_folder",
    "workspace_write_file",
    "workspace_append_file",
    "schedule_desktop_folder",
    "run_skill",
    "memory_write",
    "memory_append",
    "remember_fact",
    "consolidate_diary",
    "autonomy_cycle",
    "windows_create_daily_task",
    "set_safety_mode",
    "session_add_message",
    "cron_add",
    "cron_set_enabled",
    "cron_run_due",
    "vector_rebuild",
    "skill_record_usage",
    "skill_curate",
    "secrets_store",
    "install_startup_daemon",
    "install_startup_console",
    "triggers_create_missions",
    "session_checkpoint",
    "session_rotate",
}
UI_TOOLS = {
    "open_browser",
    "move_mouse",
    "click_mouse",
    "double_click_mouse",
    "scroll_mouse",
    "type_text",
    "press_key",
    "hotkey",
    "browser_snapshot",
    "browser_back",
    "browser_click_text",
    "browser_type_text",
    "browser_scroll",
    "browser_navigate",
    "browser_visual_steps",
}
ADMIN_TOOLS = {"admin_command", "launch_elevated_powershell"}
SELF_MODIFY_TOOLS = {"patch_core", "self_improvement_cycle"}


@dataclass(frozen=True)
class ToolPolicyDecision:
    tool: str
    approval_class: str
    auto_approve: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "approval_class": self.approval_class,
            "auto_approve": self.auto_approve,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ToolExecutionDecision:
    allowed: bool
    policy: ToolPolicyDecision
    mode: str
    reason: str
    requires_approval: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = self.policy.as_dict()
        data.update(
            {
                "allowed": self.allowed,
                "mode": self.mode,
                "execution_reason": self.reason,
                "requires_approval": self.requires_approval,
            }
        )
        return data


def classify_tool(tool: str, args: dict[str, Any] | None = None) -> ToolPolicyDecision:
    if tool in READONLY_TOOLS:
        return ToolPolicyDecision(tool, "readonly", True, "Ferramenta apenas le estado/local context.")
    if tool in SEARCH_TOOLS:
        return ToolPolicyDecision(tool, "search", True, "Pesquisa/leitura de rede; sem mutacao local direta.")
    if tool in UI_TOOLS:
        return ToolPolicyDecision(tool, "ui_control", False, "Controla UI/rato/teclado/browser e pode afetar trabalho do Sandro.")
    if tool in EXEC_TOOLS:
        return ToolPolicyDecision(tool, "exec_capable", False, "Executa processo/comando local.")
    if tool in PUBLIC_TOOLS:
        return ToolPolicyDecision(tool, "public_or_external", False, "Pode publicar, enviar ou preparar comunicacao externa.")
    if tool in ADMIN_TOOLS:
        return ToolPolicyDecision(tool, "admin", False, "Pode requerer privilegios elevados.")
    if tool in SELF_MODIFY_TOOLS:
        return ToolPolicyDecision(tool, "self_modify", False, "Pode alterar a propria Eve.")
    if tool in MUTATING_TOOLS:
        return ToolPolicyDecision(tool, "mutating", False, "Altera ficheiros, memoria, tarefas ou estado.")
    return ToolPolicyDecision(tool, "unknown", False, "Ferramenta sem classificacao explicita.")


def decide_tool_execution(tool: str, args: dict[str, Any] | None = None) -> ToolExecutionDecision:
    args = args or {}
    policy = classify_tool(tool, args)
    mode = current_safety_mode()
    profile = current_safety_profile()
    approved = bool(args.get("approved") or args.get("approval") or args.get("sandro_approved"))

    if mode == "unrestricted_mode":
        return ToolExecutionDecision(True, policy, mode, "unrestricted_mode ativo; guards internos desligados.")

    if policy.auto_approve:
        return ToolExecutionDecision(True, policy, mode, "Ferramenta auto-aprovada pela policy.")

    if approved:
        return ToolExecutionDecision(True, policy, mode, "Aprovacao explicita incluida nos argumentos.")

    if policy.approval_class == "ui_control" and profile.get("ui_control"):
        return ToolExecutionDecision(True, policy, mode, "Perfil atual permite controlo UI.")

    if policy.approval_class == "mutating" and not profile.get("action_guard", True):
        return ToolExecutionDecision(True, policy, mode, "Action guard desligado no perfil atual.")

    if policy.approval_class == "exec_capable" and not profile.get("command_guard", True):
        return ToolExecutionDecision(True, policy, mode, "Command guard desligado no perfil atual.")

    if policy.approval_class == "public_or_external":
        return ToolExecutionDecision(
            False,
            policy,
            mode,
            "Acao publica/externa sem approved=true no pedido da ferramenta.",
            requires_approval=True,
        )

    if policy.approval_class == "admin" and profile.get("admin_requires_approval", True):
        return ToolExecutionDecision(False, policy, mode, "Acao admin requer aprovacao explicita.", requires_approval=True)

    if policy.approval_class == "self_modify" and profile.get("self_modify_requires_approval", True):
        return ToolExecutionDecision(
            False,
            policy,
            mode,
            "Auto-modificacao requer aprovacao explicita.",
            requires_approval=True,
        )

    if policy.approval_class in {"exec_capable", "unknown"}:
        return ToolExecutionDecision(
            False,
            policy,
            mode,
            "Ferramenta executavel/desconhecida requer approved=true fora de unrestricted_mode.",
            requires_approval=True,
        )

    return ToolExecutionDecision(True, policy, mode, "Permitido pelo perfil atual.")
