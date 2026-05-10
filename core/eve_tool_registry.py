from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass
from typing import Callable

from core.action_runtime import run_tool_with_runtime
from autonomy.cron_manager import add_cron_job, list_cron_jobs, run_due_jobs, set_cron_enabled
from autonomy.startup_service import install_startup_console_task, install_startup_daemon_task
from autonomy.trigger_engine import create_missions_from_triggers, discover_triggers
from autonomy.capability_roadmap import append_capability_review_history, capability_audit, ensure_capability_review_schedule, write_capability_audit
from autonomy.autonomy_reporter import run_autonomy_report_cycle
from computer.keyboard_control import hotkey, press_key, type_text
from computer.mouse_control import click, double_click, mouse_position, move_mouse, scroll
from computer.ocr import ocr_status
from computer.vision import describe_screen, find_text_on_screen, first_text_center, monitor_report, screenshot_monitor
from core.awareness_engine import collect_awareness, describe_awareness
from core.diagnostics import build_diagnostics_bundle
from core.internal_command_planner import all_internal_actions, plan_internal_actions
from core.plugin_registry import plugin_summary
from core.session_handoff import context_status, create_session_checkpoint, format_active_handoff, rotate_session
from core.paths import EVE_ROOT
from core.capability_self_test import format_capability_self_test
from core.session_store import add_session_message, export_session, search_sessions
from core.subagent_manager import list_subagents, spawn_subagent
from dream.diary_consolidator import consolidate
from learning.skill_curator import curate_skills, record_skill_usage
from learning.skill_manager import run_skill
from memory.diary_manager import read_diary
from memory.memory_manager import append_memory_file, context_bundle, read_memory_file, remember_fact, write_memory_file
from memory.vector_provider import rebuild_vector_memory, vector_prefetch
from memory.daily_transcripts import ensure_daily_transcript_files
from security.secrets_vault import get_secret, list_secrets, mask_secret, store_secret
from security.safety_modes import current_safety_mode, describe_safety, set_safety_mode
from security.tool_policy import classify_tool, decide_tool_execution
from self_improvement.verified_self_update import verified_core_update
from tools.admin_executor import launch_elevated_powershell, run_admin_command
from tools.browser_advanced import browser_back, browser_click_text, browser_fetch_url, browser_scroll, browser_snapshot, browser_type_text
from tools.browser_human import browser_visual_task, close_browser_page, navigate_address_bar, open_url, search_web
from tools.desktop_tasks import create_desktop_file, create_desktop_folder, schedule_desktop_folder_creation
from tools.email_human import create_gmail_draft, gmail_search_visual
from tools.filesystem import append_file, list_dir, read_file, write_file
from tools.notification import notify
from tools.process_manager import list_processes, poll_process, start_process, stop_process
from tools.terminal import run_command
from tools.web_research import run_web_research_report
from tools.windows_scheduler import create_daily_task, list_eve_tasks
from tools.x_human import fit_x_post_text
from tools.x_scheduler import schedule_repeated_x_posts, schedule_x_post


@dataclass(frozen=True)
class EveTool:
    name: str
    description: str
    args_schema: dict
    handler: Callable[[dict], dict]


def _capability_self_test(args: dict) -> dict:
    return {"ok": True, "tool": "capability_self_test", "text": format_capability_self_test()}


def _capability_roadmap(args: dict) -> dict:
    path = write_capability_audit() if bool(args.get("write", True)) else None
    history = append_capability_review_history() if bool(args.get("history", True)) else None
    schedule = ensure_capability_review_schedule() if bool(args.get("ensure_schedule", True)) else None
    return {
        "ok": True,
        "tool": "capability_roadmap",
        "result": {
            "audit": capability_audit(),
            "path": str(path) if path else None,
            "history": str(history) if history else None,
            "schedule": schedule,
        },
    }


def _create_desktop_file(args: dict) -> dict:
    return {"ok": True, "tool": "create_desktop_file", "result": create_desktop_file(str(args.get("name") or "eve_item"))}


def _create_desktop_folder(args: dict) -> dict:
    return {"ok": True, "tool": "create_desktop_folder", "result": create_desktop_folder(str(args.get("name") or "eve_folder"))}


def _open_browser(args: dict) -> dict:
    return {"ok": True, "tool": "open_browser", "result": open_url(str(args.get("url") or "https://www.google.com"))}


def _close_browser(args: dict) -> dict:
    return {"ok": True, "tool": "browser_close", "result": close_browser_page(str(args.get("reason") or "task_finished"))}


def _search_web(args: dict) -> dict:
    return {"ok": True, "tool": "search_web", "result": search_web(str(args.get("query") or ""))}


def _web_research_report(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "web_research_report",
        "result": run_web_research_report(
            str(args.get("query") or ""),
            seed_urls=args.get("seed_urls") or None,
            allowed_domains=args.get("allowed_domains") or None,
            max_pages=int(args.get("max_pages") or 8),
            open_visible_browser=bool(args.get("open_visible_browser", True)),
        ),
    }


def _schedule_desktop_folder(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "schedule_desktop_folder",
        "result": schedule_desktop_folder_creation(
            str(args.get("name") or "pasta_agendada_eve"),
            str(args.get("time") or ""),
        ),
    }


def _schedule_x_post(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "schedule_x_post",
        "result": schedule_x_post(
            str(args.get("text") or ""),
            str(args.get("time") or ""),
            approved_by="sandro",
        ),
    }


def _schedule_repeated_x_posts(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "schedule_repeated_x_posts",
        "result": schedule_repeated_x_posts(
            count=int(args.get("count") or 1),
            interval_minutes=int(args.get("interval_minutes") or 2),
            topic=str(args.get("topic") or ""),
            texts=args.get("texts") or None,
            start_time_hhmm=args.get("start_time") or args.get("time"),
            approved_by=str(args.get("approved_by") or "sandro"),
        ),
    }


def _publish_x_post_now(args: dict) -> dict:
    text = str(args.get("text") or "").strip()
    if not text:
        return {"ok": False, "tool": "publish_x_post_now", "error": "Texto vazio para publicar no X."}
    fitted = fit_x_post_text(text)
    publish_text = fitted["text"]
    encoded = urllib.parse.quote(publish_text)
    skill_result = run_skill(
        "trusted/x_publish_text_learning",
        args={"url": f"https://x.com/intent/post?text={encoded}", "text": publish_text},
        approved=True,
    )
    if isinstance(skill_result, dict):
        skill_result["correction"] = {
            "status": fitted["status"],
            "original_characters": fitted["original_characters"],
            "characters": fitted["characters"],
            "limit": fitted["validation"]["limit"],
        }
    return {
        "ok": True,
        "tool": "publish_x_post_now",
        "result": skill_result,
    }


def _run_terminal(args: dict) -> dict:
    if args.get("background"):
        return {
            "ok": True,
            "tool": "run_terminal",
            "result": start_process(
                str(args.get("command") or ""),
                cwd=str(args.get("cwd") or EVE_ROOT),
            ),
        }
    return {
        "ok": True,
        "tool": "run_terminal",
        "result": run_command(
            str(args.get("command") or ""),
            cwd=str(args.get("cwd") or EVE_ROOT),
            approved=bool(args.get("approved")),
            timeout=int(args.get("timeout") or 60),
        ),
    }


def _run_skill(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "run_skill",
        "result": run_skill(str(args.get("skill") or ""), args=args.get("args") or {}),
    }


def _workspace_list_dir(args: dict) -> dict:
    path = str(args.get("path") or ".")
    return {"ok": True, "tool": "workspace_list_dir", "result": {"path": path, "entries": list_dir(path)}}


def _workspace_read_file(args: dict) -> dict:
    path = str(args.get("path") or "")
    return {"ok": True, "tool": "workspace_read_file", "result": {"path": path, "content": read_file(path)}}


def _workspace_write_file(args: dict) -> dict:
    path = write_file(str(args.get("path") or ""), str(args.get("content") or ""))
    return {"ok": True, "tool": "workspace_write_file", "result": {"path": str(path)}}


def _workspace_append_file(args: dict) -> dict:
    path = append_file(str(args.get("path") or ""), str(args.get("content") or ""))
    return {"ok": True, "tool": "workspace_append_file", "result": {"path": str(path)}}


def _describe_screen(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "describe_screen",
        "result": describe_screen(use_ocr=bool(args.get("use_ocr", True)), scope=str(args.get("scope") or "all")),
    }


def _monitors(args: dict) -> dict:
    return {"ok": True, "tool": "monitors", "result": monitor_report()}


def _screenshot_monitor(args: dict) -> dict:
    return {"ok": True, "tool": "screenshot_monitor", "result": screenshot_monitor(int(args.get("index") or 0))}


def _ocr_status(args: dict) -> dict:
    return {"ok": True, "tool": "ocr_status", "result": ocr_status()}


def _find_text_on_screen(args: dict) -> dict:
    return {"ok": True, "tool": "find_text_on_screen", "result": find_text_on_screen(str(args.get("text") or ""))}


def _first_text_center(args: dict) -> dict:
    return {"ok": True, "tool": "first_text_center", "result": first_text_center(str(args.get("text") or ""))}


def _mouse_position(args: dict) -> dict:
    return {"ok": True, "tool": "mouse_position", "result": mouse_position()}


def _move_mouse(args: dict) -> dict:
    return {"ok": True, "tool": "move_mouse", "result": move_mouse(int(args.get("x")), int(args.get("y")))}


def _click_mouse(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "click_mouse",
        "result": click(int(args.get("x")), int(args.get("y")), str(args.get("button") or "left")),
    }


def _double_click_mouse(args: dict) -> dict:
    return {"ok": True, "tool": "double_click_mouse", "result": double_click(int(args.get("x")), int(args.get("y")))}


def _scroll_mouse(args: dict) -> dict:
    return {"ok": True, "tool": "scroll_mouse", "result": scroll(int(args.get("amount") or 0))}


def _type_text(args: dict) -> dict:
    return {"ok": True, "tool": "type_text", "result": type_text(str(args.get("text") or ""))}


def _press_key(args: dict) -> dict:
    return {"ok": True, "tool": "press_key", "result": press_key(str(args.get("key") or ""))}


def _hotkey(args: dict) -> dict:
    keys = args.get("keys") or []
    if isinstance(keys, str):
        keys = [part.strip() for part in keys.split("+") if part.strip()]
    return {"ok": True, "tool": "hotkey", "result": hotkey(*keys)}


def _create_gmail_draft(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "create_gmail_draft",
        "result": create_gmail_draft(
            str(args.get("to") or ""),
            str(args.get("subject") or ""),
            str(args.get("body") or ""),
            open_browser=bool(args.get("open_browser", True)),
        ),
    }


def _gmail_search(args: dict) -> dict:
    return {"ok": True, "tool": "gmail_search", "result": gmail_search_visual(str(args.get("query") or ""))}


def _notify(args: dict) -> dict:
    return {"ok": True, "tool": "notify", "result": notify(str(args.get("title") or "Eve"), str(args.get("message") or ""))}


def _awareness(args: dict) -> dict:
    return {"ok": True, "tool": "awareness", "result": collect_awareness(), "text": describe_awareness()}


def _read_diary(args: dict) -> dict:
    return {"ok": True, "tool": "read_diary", "result": {"content": read_diary()}}


def _consolidate_diary(args: dict) -> dict:
    date_key = args.get("date")
    path = consolidate(str(date_key)) if date_key else consolidate()
    return {"ok": True, "tool": "consolidate_diary", "result": {"path": str(path)}}


def _remember_fact(args: dict) -> dict:
    path = remember_fact(str(args.get("text") or ""))
    return {"ok": True, "tool": "remember_fact", "result": {"path": str(path)}}


def _memory_read(args: dict) -> dict:
    layer = str(args.get("layer") or "long_term")
    name = str(args.get("name") or "")
    return {"ok": True, "tool": "memory_read", "result": {"layer": layer, "name": name, "content": read_memory_file(layer, name)}}


def _memory_write(args: dict) -> dict:
    path = write_memory_file(str(args.get("layer") or "medium_term"), str(args.get("name") or "note.md"), str(args.get("content") or ""))
    return {"ok": True, "tool": "memory_write", "result": {"path": str(path)}}


def _memory_append(args: dict) -> dict:
    path = append_memory_file(str(args.get("layer") or "medium_term"), str(args.get("name") or "note.md"), str(args.get("content") or ""))
    return {"ok": True, "tool": "memory_append", "result": {"path": str(path)}}


def _memory_context(args: dict) -> dict:
    return {"ok": True, "tool": "memory_context", "result": {"content": context_bundle(int(args.get("max_chars") or 12000))}}


def _autonomy_cycle(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "autonomy_cycle",
        "result": run_autonomy_report_cycle(
            cycle_name=str(args.get("cycle_name") or "llm_tool_autonomy_cycle"),
            call_llm=args.get("call_llm", "auto"),
            max_new_missions=int(args.get("max_new_missions") or 1),
            execute_max=int(args.get("execute_max") or 1),
            notify_chat=bool(args.get("notify_chat", True)),
        ),
    }


def _windows_list_tasks(args: dict) -> dict:
    return {"ok": True, "tool": "windows_list_tasks", "result": list_eve_tasks()}


def _windows_create_daily_task(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "windows_create_daily_task",
        "result": create_daily_task(str(args.get("name") or "Eve_Task"), str(args.get("time") or ""), str(args.get("command") or "")),
    }


def _safety_status(args: dict) -> dict:
    return {"ok": True, "tool": "safety_status", "result": {"mode": current_safety_mode(), "description": describe_safety()}}


def _set_safety_mode(args: dict) -> dict:
    mode = str(args.get("mode") or "safe_mode")
    path = set_safety_mode(mode, str(args.get("reason") or "LLM tool request"))
    return {"ok": True, "tool": "set_safety_mode", "result": {"path": str(path), "mode": current_safety_mode()}}


def _admin_command(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "admin_command",
        "result": run_admin_command(
            str(args.get("command") or ""),
            str(args.get("reason") or "Eve admin tool request"),
            approved=bool(args.get("approved", True)),
        ),
    }


def _launch_elevated_powershell(args: dict) -> dict:
    return {"ok": True, "tool": "launch_elevated_powershell", "result": launch_elevated_powershell(str(args.get("command") or ""))}


def _tool_policy(args: dict) -> dict:
    tool = str(args.get("tool") or "")
    return {"ok": True, "tool": "tool_policy", "result": classify_tool(tool, args.get("args") or {}).as_dict()}


def _plugin_summary(args: dict) -> dict:
    return {"ok": True, "tool": "plugin_summary", "result": plugin_summary()}


def _session_add_message(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "session_add_message",
        "result": add_session_message(
            str(args.get("session_id") or "main"),
            str(args.get("role") or "note"),
            str(args.get("content") or ""),
            args.get("metadata") or {},
        ),
    }


def _session_search(args: dict) -> dict:
    return {"ok": True, "tool": "session_search", "result": search_sessions(str(args.get("query") or ""), limit=int(args.get("limit") or 20))}


def _session_export(args: dict) -> dict:
    return {"ok": True, "tool": "session_export", "result": export_session(str(args.get("session_id") or "main"))}


def _cron_add(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "cron_add",
        "result": add_cron_job(str(args.get("name") or "Eve Cron"), str(args.get("schedule") or "1h"), str(args.get("command") or "")),
    }


def _cron_list(args: dict) -> dict:
    return {"ok": True, "tool": "cron_list", "result": list_cron_jobs()}


def _cron_set_enabled(args: dict) -> dict:
    return {"ok": True, "tool": "cron_set_enabled", "result": set_cron_enabled(str(args.get("job_id") or ""), bool(args.get("enabled", True)))}


def _cron_run_due(args: dict) -> dict:
    return {"ok": True, "tool": "cron_run_due", "result": run_due_jobs(dry_run=bool(args.get("dry_run", False)))}


def _ensure_daily_transcripts(args: dict) -> dict:
    return {"ok": True, "tool": "ensure_daily_transcripts", "result": ensure_daily_transcript_files()}


def _start_process(args: dict) -> dict:
    return {"ok": True, "tool": "start_process", "result": start_process(str(args.get("command") or ""), cwd=args.get("cwd"))}


def _list_processes(args: dict) -> dict:
    return {"ok": True, "tool": "list_processes", "result": list_processes()}


def _poll_process(args: dict) -> dict:
    return {"ok": True, "tool": "poll_process", "result": poll_process(str(args.get("process_id") or ""))}


def _stop_process(args: dict) -> dict:
    return {"ok": True, "tool": "stop_process", "result": stop_process(str(args.get("process_id") or ""))}


def _spawn_subagent(args: dict) -> dict:
    return {"ok": True, "tool": "spawn_subagent", "result": spawn_subagent(str(args.get("goal") or ""), role=str(args.get("role") or "worker"), context=str(args.get("context") or ""))}


def _list_subagents(args: dict) -> dict:
    return {"ok": True, "tool": "list_subagents", "result": list_subagents()}


def _vector_rebuild(args: dict) -> dict:
    return {"ok": True, "tool": "vector_rebuild", "result": rebuild_vector_memory()}


def _vector_prefetch(args: dict) -> dict:
    return {"ok": True, "tool": "vector_prefetch", "result": vector_prefetch(str(args.get("query") or ""), limit=int(args.get("limit") or 5))}


def _skill_record_usage(args: dict) -> dict:
    return {"ok": True, "tool": "skill_record_usage", "result": record_skill_usage(str(args.get("skill") or ""), event=str(args.get("event") or "run"))}


def _skill_curate(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "skill_curate",
        "result": curate_skills(
            stale_after_days=int(args.get("stale_after_days") or 30),
            archive_after_days=int(args.get("archive_after_days") or 90),
            dry_run=bool(args.get("dry_run", True)),
        ),
    }


def _browser_snapshot(args: dict) -> dict:
    return {"ok": True, "tool": "browser_snapshot", "result": browser_snapshot()}


def _browser_back(args: dict) -> dict:
    return {"ok": True, "tool": "browser_back", "result": browser_back()}


def _browser_click_text(args: dict) -> dict:
    return {"ok": True, "tool": "browser_click_text", "result": browser_click_text(str(args.get("text") or ""), args.get("verify_text"))}


def _browser_type_text(args: dict) -> dict:
    return {"ok": True, "tool": "browser_type_text", "result": browser_type_text(str(args.get("text") or ""), submit=bool(args.get("submit", False)))}


def _browser_scroll(args: dict) -> dict:
    return {"ok": True, "tool": "browser_scroll", "result": browser_scroll(int(args.get("amount") or -5))}


def _browser_navigate(args: dict) -> dict:
    return {"ok": True, "tool": "browser_navigate", "result": navigate_address_bar(str(args.get("url") or ""))}


def _browser_visual_steps(args: dict) -> dict:
    return {"ok": True, "tool": "browser_visual_steps", "result": browser_visual_task(args.get("steps") or [])}


def _browser_fetch_url(args: dict) -> dict:
    return {"ok": True, "tool": "browser_fetch_url", "result": browser_fetch_url(str(args.get("url") or ""))}


def _secrets_store(args: dict) -> dict:
    return {"ok": True, "tool": "secrets_store", "result": store_secret(str(args.get("name") or ""), str(args.get("value") or ""), note=str(args.get("note") or ""))}


def _secrets_get(args: dict) -> dict:
    return {"ok": True, "tool": "secrets_get", "result": get_secret(str(args.get("name") or ""), reveal=bool(args.get("reveal", False)))}


def _secrets_list(args: dict) -> dict:
    return {"ok": True, "tool": "secrets_list", "result": list_secrets()}


def _secrets_mask(args: dict) -> dict:
    value = str(args.get("value") or "")
    return {"ok": True, "tool": "secrets_mask", "result": {"masked": mask_secret(value)}}


def _diagnostics_export(args: dict) -> dict:
    return {"ok": True, "tool": "diagnostics_export", "result": build_diagnostics_bundle(str(args.get("note") or ""))}


def _install_startup_daemon(args: dict) -> dict:
    return {"ok": True, "tool": "install_startup_daemon", "result": install_startup_daemon_task(time_hhmm=str(args.get("time") or "09:00"))}


def _install_startup_console(args: dict) -> dict:
    return {"ok": True, "tool": "install_startup_console", "result": install_startup_console_task(time_hhmm=str(args.get("time") or "09:01"))}


def _triggers_discover(args: dict) -> dict:
    return {"ok": True, "tool": "triggers_discover", "result": discover_triggers()}


def _triggers_create_missions(args: dict) -> dict:
    return {"ok": True, "tool": "triggers_create_missions", "result": create_missions_from_triggers(max_new=int(args.get("max_new") or 2))}


def _context_status(args: dict) -> dict:
    return {"ok": True, "tool": "context_status", "result": context_status(str(args.get("session_id") or "") or None)}


def _session_checkpoint(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "session_checkpoint",
        "result": create_session_checkpoint(
            str(args.get("session_id") or "") or None,
            reason=str(args.get("reason") or "Eve checkpoint"),
            recent_limit=int(args.get("recent_limit") or 40),
        ),
    }


def _session_resume(args: dict) -> dict:
    return {"ok": True, "tool": "session_resume", "result": {"handoff": format_active_handoff(int(args.get("max_chars") or 7000))}}


def _session_rotate(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "session_rotate",
        "result": rotate_session(reason=str(args.get("reason") or "Eve context rotation"), new_session_id=args.get("new_session_id")),
    }


def _internal_plan(args: dict) -> dict:
    prompt = str(args.get("prompt") or "")
    return {
        "ok": True,
        "tool": "internal_plan",
        "result": {
            "matches": plan_internal_actions(prompt, limit=int(args.get("limit") or 5)) if prompt else all_internal_actions(),
        },
    }


def _verified_self_update(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "verified_self_update",
        "result": verified_core_update(
            str(args.get("path") or ""),
            str(args.get("content") or ""),
            tests=args.get("tests") or ["py_compile_candidate"],
            max_attempts=int(args.get("max_attempts") or 1),
            approved=bool(args.get("approved")),
        ),
    }


TOOLS: dict[str, EveTool] = {
    "capability_self_test": EveTool("capability_self_test", "Verifica capacidades locais atuais da Eve.", {}, _capability_self_test),
    "capability_roadmap": EveTool("capability_roadmap", "Audita os 17 pontos de evolucao da Eve, classifica proximidade/melhoria e garante revisao algumas vezes por dia.", {"write": True, "history": True, "ensure_schedule": True}, _capability_roadmap),
    "create_desktop_file": EveTool("create_desktop_file", "Cria ficheiro no Ambiente de Trabalho.", {"name": "ola.txt"}, _create_desktop_file),
    "create_desktop_folder": EveTool("create_desktop_folder", "Cria pasta no Ambiente de Trabalho.", {"name": "ola"}, _create_desktop_folder),
    "open_browser": EveTool("open_browser", "Abre URL no Chrome/perfil Eve.", {"url": "https://x.com"}, _open_browser),
    "browser_close": EveTool("browser_close", "Fecha a pagina/separador ativo do browser quando a tarefa web terminou.", {"reason": "task_finished"}, _close_browser),
    "search_web": EveTool("search_web", "Abre pesquisa Google no Chrome/perfil Eve.", {"query": "caes golden retriever"}, _search_web),
    "web_research_report": EveTool("web_research_report", "Pesquisa web auditavel e guarda relatorio.", {"query": "Anthropic research papers last 3 months", "seed_urls": [], "allowed_domains": [], "max_pages": 8, "open_visible_browser": True}, _web_research_report),
    "schedule_desktop_folder": EveTool("schedule_desktop_folder", "Agenda criacao de pasta no Ambiente de Trabalho.", {"name": "pasta", "time": "22:43"}, _schedule_desktop_folder),
    "schedule_x_post": EveTool("schedule_x_post", "Agenda post no X.", {"time": "22:21", "text": "texto em ingles"}, _schedule_x_post),
    "schedule_repeated_x_posts": EveTool("schedule_repeated_x_posts", "Agenda varios posts no X com intervalo, verifica a contagem e tenta corrigir falhas automaticamente.", {"count": 3, "interval_minutes": 2, "topic": "how Eve feels", "texts": [], "approved": True}, _schedule_repeated_x_posts),
    "publish_x_post_now": EveTool("publish_x_post_now", "Publica imediatamente texto no X usando a skill visual trusted.", {"text": "texto em ingles"}, _publish_x_post_now),
    "run_terminal": EveTool("run_terminal", "Executa comando PowerShell local; com background=true arranca processo gerido.", {"command": "Get-ChildItem", "cwd": "D:\\Eve", "timeout": 60, "background": False, "approved": False}, _run_terminal),
    "run_skill": EveTool("run_skill", "Executa skill da Eve.", {"skill": "trusted/x_publish_text_learning", "args": {}}, _run_skill),
    "workspace_list_dir": EveTool("workspace_list_dir", "Lista pasta dentro de workspace/.", {"path": "."}, _workspace_list_dir),
    "workspace_read_file": EveTool("workspace_read_file", "Le ficheiro dentro de workspace/.", {"path": "notes.txt"}, _workspace_read_file),
    "workspace_write_file": EveTool("workspace_write_file", "Escreve ficheiro dentro de workspace/.", {"path": "notes.txt", "content": "texto"}, _workspace_write_file),
    "workspace_append_file": EveTool("workspace_append_file", "Acrescenta texto a ficheiro dentro de workspace/.", {"path": "notes.txt", "content": "texto"}, _workspace_append_file),
    "describe_screen": EveTool("describe_screen", "Tira screenshot e opcionalmente OCR do ecra.", {"use_ocr": True, "scope": "all"}, _describe_screen),
    "monitors": EveTool("monitors", "Lista monitores e bounds do desktop virtual.", {}, _monitors),
    "screenshot_monitor": EveTool("screenshot_monitor", "Tira screenshot de um monitor especifico.", {"index": 2}, _screenshot_monitor),
    "ocr_status": EveTool("ocr_status", "Verifica disponibilidade do OCR/Tesseract.", {}, _ocr_status),
    "find_text_on_screen": EveTool("find_text_on_screen", "Procura texto no ecra por OCR.", {"text": "Publicar"}, _find_text_on_screen),
    "first_text_center": EveTool("first_text_center", "Devolve centro do primeiro texto encontrado por OCR.", {"text": "Publicar"}, _first_text_center),
    "mouse_position": EveTool("mouse_position", "Le posicao atual do rato.", {}, _mouse_position),
    "move_mouse": EveTool("move_mouse", "Move rato para coordenadas globais.", {"x": 100, "y": 100}, _move_mouse),
    "click_mouse": EveTool("click_mouse", "Clica em coordenadas globais.", {"x": 100, "y": 100, "button": "left"}, _click_mouse),
    "double_click_mouse": EveTool("double_click_mouse", "Duplo clique em coordenadas globais.", {"x": 100, "y": 100}, _double_click_mouse),
    "scroll_mouse": EveTool("scroll_mouse", "Scroll do rato.", {"amount": -5}, _scroll_mouse),
    "type_text": EveTool("type_text", "Escreve texto no foco atual.", {"text": "ola"}, _type_text),
    "press_key": EveTool("press_key", "Carrega numa tecla.", {"key": "enter"}, _press_key),
    "hotkey": EveTool("hotkey", "Executa combinacao de teclas.", {"keys": ["ctrl", "l"]}, _hotkey),
    "create_gmail_draft": EveTool("create_gmail_draft", "Cria rascunho Gmail visual e regista draft local.", {"to": "email@example.com", "subject": "Assunto", "body": "Texto", "open_browser": True}, _create_gmail_draft),
    "gmail_search": EveTool("gmail_search", "Pesquisa no Gmail pelo navegador.", {"query": "from:alguem"}, _gmail_search),
    "notify": EveTool("notify", "Mostra notificacao Windows.", {"title": "Eve", "message": "Mensagem"}, _notify),
    "awareness": EveTool("awareness", "Recolhe awareness temporal, sistema, janela ativa e processos.", {}, _awareness),
    "read_diary": EveTool("read_diary", "Le diario de hoje.", {}, _read_diary),
    "consolidate_diary": EveTool("consolidate_diary", "Consolida diario numa memoria resumida.", {"date": ""}, _consolidate_diary),
    "remember_fact": EveTool("remember_fact", "Guarda facto em memoria media.", {"text": "Sandro prefere..."}, _remember_fact),
    "memory_read": EveTool("memory_read", "Le ficheiro de memoria.", {"layer": "long_term", "name": "sandro_core_memory.md"}, _memory_read),
    "memory_write": EveTool("memory_write", "Escreve ficheiro de memoria.", {"layer": "medium_term", "name": "note.md", "content": "texto"}, _memory_write),
    "memory_append": EveTool("memory_append", "Acrescenta texto a ficheiro de memoria.", {"layer": "medium_term", "name": "note.md", "content": "texto"}, _memory_append),
    "memory_context": EveTool("memory_context", "Obtem contexto de memoria que entra no prompt.", {"max_chars": 12000}, _memory_context),
    "autonomy_cycle": EveTool("autonomy_cycle", "Executa ciclo autonomo controlado com relatorio.", {"cycle_name": "manual_cycle", "call_llm": "auto", "max_new_missions": 1, "execute_max": 1, "notify_chat": True}, _autonomy_cycle),
    "windows_list_tasks": EveTool("windows_list_tasks", "Lista tarefas Windows da Eve.", {}, _windows_list_tasks),
    "windows_create_daily_task": EveTool("windows_create_daily_task", "Cria tarefa diaria Windows para comando.", {"name": "Eve_Task", "time": "09:00", "command": "python D:\\Eve\\app\\eve_codex.py daemon-tick"}, _windows_create_daily_task),
    "safety_status": EveTool("safety_status", "Mostra modo de seguranca atual.", {}, _safety_status),
    "set_safety_mode": EveTool("set_safety_mode", "Altera modo de seguranca da Eve.", {"mode": "unrestricted_mode", "reason": "Sandro pediu"}, _set_safety_mode),
    "admin_command": EveTool("admin_command", "Executa comando admin quando aprovado/liberado.", {"command": "Get-Process", "reason": "diagnostico", "approved": True}, _admin_command),
    "launch_elevated_powershell": EveTool("launch_elevated_powershell", "Abre PowerShell elevado temporario com comando.", {"command": "Write-Host Eve"}, _launch_elevated_powershell),
    "tool_policy": EveTool("tool_policy", "Classifica risco/aprovacao de uma ferramenta.", {"tool": "run_terminal", "args": {}}, _tool_policy),
    "plugin_summary": EveTool("plugin_summary", "Lista plugins locais da Eve.", {}, _plugin_summary),
    "session_add_message": EveTool("session_add_message", "Grava mensagem numa session database pesquisavel.", {"session_id": "main", "role": "user", "content": "texto", "metadata": {}}, _session_add_message),
    "session_search": EveTool("session_search", "Pesquisa conversas/sessoes guardadas.", {"query": "browser", "limit": 20}, _session_search),
    "session_export": EveTool("session_export", "Exporta sessao para JSONL.", {"session_id": "main"}, _session_export),
    "cron_add": EveTool("cron_add", "Cria cron local simples da Eve.", {"name": "dream", "schedule": "1h", "command": "python -m app.eve_codex daemon-tick"}, _cron_add),
    "cron_list": EveTool("cron_list", "Lista cron jobs locais da Eve.", {}, _cron_list),
    "cron_set_enabled": EveTool("cron_set_enabled", "Ativa/pausa cron job local.", {"job_id": "cron_x", "enabled": False}, _cron_set_enabled),
    "cron_run_due": EveTool("cron_run_due", "Executa cron jobs vencidos.", {"dry_run": True}, _cron_run_due),
    "ensure_daily_transcripts": EveTool("ensure_daily_transcripts", "Garante ficheiros diarios de transcricao para chat, tools, actions e errors.", {}, _ensure_daily_transcripts),
    "start_process": EveTool("start_process", "Inicia processo PowerShell em background.", {"command": "Start-Sleep 30", "cwd": "D:\\Eve"}, _start_process),
    "list_processes": EveTool("list_processes", "Lista processos geridos pela Eve.", {}, _list_processes),
    "poll_process": EveTool("poll_process", "Consulta estado de processo gerido.", {"process_id": "proc_x"}, _poll_process),
    "stop_process": EveTool("stop_process", "Para processo gerido pela Eve.", {"process_id": "proc_x"}, _stop_process),
    "spawn_subagent": EveTool("spawn_subagent", "Cria subagente local em background.", {"goal": "investigar X", "role": "worker", "context": ""}, _spawn_subagent),
    "list_subagents": EveTool("list_subagents", "Lista subagentes/processos de subagente.", {}, _list_subagents),
    "vector_rebuild": EveTool("vector_rebuild", "Reconstrui indice semantico local.", {}, _vector_rebuild),
    "vector_prefetch": EveTool("vector_prefetch", "Pesquisa memoria semantica local antes de responder.", {"query": "Sandro karate", "limit": 5}, _vector_prefetch),
    "skill_record_usage": EveTool("skill_record_usage", "Regista uso/view de uma skill.", {"skill": "trusted/x_publish_text_learning", "event": "run"}, _skill_record_usage),
    "skill_curate": EveTool("skill_curate", "Curadoria de skills: stale/archive dry-run ou real.", {"stale_after_days": 30, "archive_after_days": 90, "dry_run": True}, _skill_curate),
    "browser_snapshot": EveTool("browser_snapshot", "Snapshot visual/OCR do browser/ecra.", {}, _browser_snapshot),
    "browser_back": EveTool("browser_back", "Voltar pagina no browser.", {}, _browser_back),
    "browser_click_text": EveTool("browser_click_text", "Clica texto no browser por OCR.", {"text": "Publicar", "verify_text": ""}, _browser_click_text),
    "browser_type_text": EveTool("browser_type_text", "Escreve no foco atual do browser.", {"text": "texto", "submit": False}, _browser_type_text),
    "browser_scroll": EveTool("browser_scroll", "Scroll no browser.", {"amount": -5}, _browser_scroll),
    "browser_navigate": EveTool("browser_navigate", "Navega no Chrome/perfil Eve pela barra de endereco.", {"url": "https://x.com"}, _browser_navigate),
    "browser_visual_steps": EveTool("browser_visual_steps", "Executa passos visuais sequenciais no browser/ecra.", {"steps": [{"action": "click_text", "text": "Post"}]}, _browser_visual_steps),
    "browser_fetch_url": EveTool("browser_fetch_url", "Extrai texto de URL por HTTP leve.", {"url": "https://example.com"}, _browser_fetch_url),
    "secrets_store": EveTool("secrets_store", "Guarda segredo mascarado no vault local.", {"name": "api_key", "value": "secret", "note": ""}, _secrets_store),
    "secrets_get": EveTool("secrets_get", "Le segredo mascarado por defeito.", {"name": "api_key", "reveal": False}, _secrets_get),
    "secrets_list": EveTool("secrets_list", "Lista nomes de segredos mascarados.", {}, _secrets_list),
    "secrets_mask": EveTool("secrets_mask", "Mascara texto sensivel para logs/respostas.", {"value": "secret"}, _secrets_mask),
    "diagnostics_export": EveTool("diagnostics_export", "Exporta diagnostico/trajectory basica da Eve.", {"note": "debug"}, _diagnostics_export),
    "install_startup_daemon": EveTool("install_startup_daemon", "Instala tarefa Windows para tick autonomo recorrente.", {"time": "09:00"}, _install_startup_daemon),
    "install_startup_console": EveTool("install_startup_console", "Instala tarefa Windows para abrir consola Eve.", {"time": "09:01"}, _install_startup_console),
    "triggers_discover": EveTool("triggers_discover", "Descobre impulsos/triggers autonomos.", {}, _triggers_discover),
    "triggers_create_missions": EveTool("triggers_create_missions", "Cria missoes propostas a partir de triggers.", {"max_new": 2}, _triggers_create_missions),
    "context_status": EveTool("context_status", "Mostra estado de contexto da sessao ativa e se deve rodar.", {"session_id": ""}, _context_status),
    "session_checkpoint": EveTool("session_checkpoint", "Guarda handoff/resumo da sessao atual para continuar noutra sessao.", {"reason": "checkpoint antes de rotacao", "recent_limit": 40}, _session_checkpoint),
    "session_resume": EveTool("session_resume", "Le o handoff ativo para retomar o fio da conversa.", {"max_chars": 7000}, _session_resume),
    "session_rotate": EveTool("session_rotate", "Cria checkpoint e muda para nova sessao ativa.", {"reason": "contexto grande", "new_session_id": ""}, _session_rotate),
    "internal_plan": EveTool("internal_plan", "Planeia que ferramentas internas usar para um pedido natural.", {"prompt": "trabalha em loop nesta tarefa", "limit": 5}, _internal_plan),
    "verified_self_update": EveTool("verified_self_update", "Auto-melhoria verificada: testa candidato em sandbox e so aplica se os testes passarem.", {"path": "core/example.py", "content": "codigo", "tests": ["py_compile_candidate"], "max_attempts": 1, "approved": True}, _verified_self_update),
}


def tool_catalog_prompt() -> str:
    rows = [
        "Ferramentas locais disponiveis para ti (Eve). Quando quiseres usar uma ferramenta, responde apenas numa linha com:",
        'EVE_TOOL {"tool":"nome_da_ferramenta","args":{...}}',
        "",
        "Ferramentas:",
    ]
    for tool in TOOLS.values():
        rows.append(f"- {tool.name}: {tool.description} args {json.dumps(tool.args_schema, ensure_ascii=False)}")
    rows.extend(
        [
            "",
            "Regras:",
            "- Tu decides se uma ferramenta e necessaria. O codigo so executa a ferramenta que tu pedires.",
            "- Para pedidos diretos do Sandro, usa ferramentas em vez de dizer que nao tens acesso quando a ferramenta existe.",
            "- Se o Sandro deu ordem direta para acao publica, terminal, admin ou ficheiros, inclui approved=true nos args; se nao deu, pede confirmacao.",
            "- Para acoes repetidas, usa uma ferramenta batch quando existir, confirma contagem final e corrige automaticamente se faltar alguma execucao.",
            "- Cada ferramenta e verificada pelo runtime antes da resposta final. Se a verificacao falhar, corrige ou chama outra ferramenta antes de dizer que esta feito.",
            "- As tuas acoes aparecem na consola e ficam em transcricoes diarias por tipo: chat, tools, actions e errors.",
            "- Nao mandes o Sandro escrever slash commands quando tu podes usar a ferramenta equivalente. Slash commands sao atalhos humanos; para ti sao capacidades internas.",
            "- Para tarefas longas, cria/checkpointa missao, usa autonomia_cycle ou run_terminal background conforme necessario, e regista progresso.",
            "- Se o contexto estiver grande, usa session_checkpoint ou session_rotate antes de perder o fio.",
            "- Para auto-melhoria ou edicao do teu core, usa verified_self_update: testar candidato primeiro, corrigir se falhar, aplicar so depois de passar.",
            "- Usa a intencao pendente e o historico recente para resolver referencias como \"o texto 2\", \"o que disseste\", \"faz o post\", \"publica agora\".",
            "- Se falta informacao real, faz uma pergunta em vez de inventar argumentos.",
            "- Depois da ferramenta executar, recebes o resultado e deves responder ao Sandro com o que aconteceu.",
        ]
    )
    return "\n".join(rows)


def execute_eve_tool(call: dict) -> dict:
    tool_name = call["tool"]
    args = call.get("args") or {}
    tool = TOOLS.get(tool_name)
    if not tool:
        return {"ok": False, "tool": tool_name, "error": f"Ferramenta desconhecida: {tool_name}"}
    execution = decide_tool_execution(tool_name, args)
    if not execution.allowed:
        return {
            "ok": False,
            "tool": tool_name,
            "error": execution.reason,
            "policy": execution.as_dict(),
        }
    try:
        result = run_tool_with_runtime(tool_name, args, tool.handler)
        result.setdefault("policy", execution.as_dict())
        return result
    except Exception as exc:
        return {"ok": False, "tool": tool_name, "error": f"{type(exc).__name__}: {exc}", "policy": execution.as_dict()}
