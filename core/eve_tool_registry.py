from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass
from typing import Callable

from autonomy.autonomy_reporter import run_autonomy_report_cycle
from computer.keyboard_control import hotkey, press_key, type_text
from computer.mouse_control import click, double_click, mouse_position, move_mouse, scroll
from computer.ocr import ocr_status
from computer.vision import describe_screen, find_text_on_screen, first_text_center, monitor_report, screenshot_monitor
from core.awareness_engine import collect_awareness, describe_awareness
from core.paths import EVE_ROOT
from core.capability_self_test import format_capability_self_test
from dream.diary_consolidator import consolidate
from learning.skill_manager import run_skill
from memory.diary_manager import read_diary
from memory.memory_manager import append_memory_file, context_bundle, read_memory_file, remember_fact, write_memory_file
from security.safety_modes import current_safety_mode, describe_safety, set_safety_mode
from tools.admin_executor import launch_elevated_powershell, run_admin_command
from tools.browser_human import open_url, search_web
from tools.desktop_tasks import create_desktop_file, create_desktop_folder, schedule_desktop_folder_creation
from tools.email_human import create_gmail_draft, gmail_search_visual
from tools.filesystem import append_file, list_dir, read_file, write_file
from tools.notification import notify
from tools.terminal import run_command
from tools.web_research import run_web_research_report
from tools.windows_scheduler import create_daily_task, list_eve_tasks
from tools.x_scheduler import schedule_x_post


@dataclass(frozen=True)
class EveTool:
    name: str
    description: str
    args_schema: dict
    handler: Callable[[dict], dict]


def _capability_self_test(args: dict) -> dict:
    return {"ok": True, "tool": "capability_self_test", "text": format_capability_self_test()}


def _create_desktop_file(args: dict) -> dict:
    return {"ok": True, "tool": "create_desktop_file", "result": create_desktop_file(str(args.get("name") or "eve_item"))}


def _create_desktop_folder(args: dict) -> dict:
    return {"ok": True, "tool": "create_desktop_folder", "result": create_desktop_folder(str(args.get("name") or "eve_folder"))}


def _open_browser(args: dict) -> dict:
    return {"ok": True, "tool": "open_browser", "result": open_url(str(args.get("url") or "https://www.google.com"))}


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


def _publish_x_post_now(args: dict) -> dict:
    text = str(args.get("text") or "").strip()
    if not text:
        return {"ok": False, "tool": "publish_x_post_now", "error": "Texto vazio para publicar no X."}
    encoded = urllib.parse.quote(text)
    return {
        "ok": True,
        "tool": "publish_x_post_now",
        "result": run_skill(
            "trusted/x_publish_text_learning",
            args={"url": f"https://x.com/intent/post?text={encoded}", "text": text},
            approved=True,
        ),
    }


def _run_terminal(args: dict) -> dict:
    return {
        "ok": True,
        "tool": "run_terminal",
        "result": run_command(
            str(args.get("command") or ""),
            cwd=str(args.get("cwd") or EVE_ROOT),
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


TOOLS: dict[str, EveTool] = {
    "capability_self_test": EveTool("capability_self_test", "Verifica capacidades locais atuais da Eve.", {}, _capability_self_test),
    "create_desktop_file": EveTool("create_desktop_file", "Cria ficheiro no Ambiente de Trabalho.", {"name": "ola.txt"}, _create_desktop_file),
    "create_desktop_folder": EveTool("create_desktop_folder", "Cria pasta no Ambiente de Trabalho.", {"name": "ola"}, _create_desktop_folder),
    "open_browser": EveTool("open_browser", "Abre URL no Chrome/perfil Eve.", {"url": "https://x.com"}, _open_browser),
    "search_web": EveTool("search_web", "Abre pesquisa Google no Chrome/perfil Eve.", {"query": "caes golden retriever"}, _search_web),
    "web_research_report": EveTool("web_research_report", "Pesquisa web auditavel e guarda relatorio.", {"query": "Anthropic research papers last 3 months", "seed_urls": [], "allowed_domains": [], "max_pages": 8, "open_visible_browser": True}, _web_research_report),
    "schedule_desktop_folder": EveTool("schedule_desktop_folder", "Agenda criacao de pasta no Ambiente de Trabalho.", {"name": "pasta", "time": "22:43"}, _schedule_desktop_folder),
    "schedule_x_post": EveTool("schedule_x_post", "Agenda post no X.", {"time": "22:21", "text": "texto em ingles"}, _schedule_x_post),
    "publish_x_post_now": EveTool("publish_x_post_now", "Publica imediatamente texto no X usando a skill visual trusted.", {"text": "texto em ingles"}, _publish_x_post_now),
    "run_terminal": EveTool("run_terminal", "Executa comando PowerShell local.", {"command": "Get-ChildItem", "cwd": "D:\\Eve", "timeout": 60}, _run_terminal),
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
    try:
        return tool.handler(args)
    except Exception as exc:
        return {"ok": False, "tool": tool_name, "error": f"{type(exc).__name__}: {exc}"}
