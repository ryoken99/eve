from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass
from typing import Callable

from core.paths import EVE_ROOT
from core.capability_self_test import format_capability_self_test
from learning.skill_manager import run_skill
from tools.browser_human import open_url
from tools.desktop_tasks import create_desktop_file, create_desktop_folder, schedule_desktop_folder_creation
from tools.terminal import run_command
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


TOOLS: dict[str, EveTool] = {
    "capability_self_test": EveTool("capability_self_test", "Verifica capacidades locais atuais da Eve.", {}, _capability_self_test),
    "create_desktop_file": EveTool("create_desktop_file", "Cria ficheiro no Ambiente de Trabalho.", {"name": "ola.txt"}, _create_desktop_file),
    "create_desktop_folder": EveTool("create_desktop_folder", "Cria pasta no Ambiente de Trabalho.", {"name": "ola"}, _create_desktop_folder),
    "open_browser": EveTool("open_browser", "Abre URL no Chrome/perfil Eve.", {"url": "https://x.com"}, _open_browser),
    "schedule_desktop_folder": EveTool("schedule_desktop_folder", "Agenda criacao de pasta no Ambiente de Trabalho.", {"name": "pasta", "time": "22:43"}, _schedule_desktop_folder),
    "schedule_x_post": EveTool("schedule_x_post", "Agenda post no X.", {"time": "22:21", "text": "texto em ingles"}, _schedule_x_post),
    "publish_x_post_now": EveTool("publish_x_post_now", "Publica imediatamente texto no X usando a skill visual trusted.", {"text": "texto em ingles"}, _publish_x_post_now),
    "run_terminal": EveTool("run_terminal", "Executa comando PowerShell local.", {"command": "Get-ChildItem", "cwd": "D:\\Eve", "timeout": 60}, _run_terminal),
    "run_skill": EveTool("run_skill", "Executa skill da Eve.", {"skill": "trusted/x_publish_text_learning", "args": {}}, _run_skill),
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

