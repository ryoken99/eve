import argparse
import base64
import json
import os
import re
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from memory.diary_manager import append_chat, chat_log_path, list_diary_days, read_diary
from memory.daily_transcripts import append_console_transcript, append_interface_transcript, append_transcript
from memory.memory_manager import consolidate_today, context_bundle, remember_fact
from tools.filesystem import append_file, list_dir, read_file, write_file
from tools.terminal import run_command
from learning.skill_manager import list_skills, promote_skill, run_skill
from learning.learn_mode import create_skill_from_demonstration
from dream.memory_reorganizer import run_dream
from dream.dream_cycle import run_dream_cycle
from research.research_notes import append_research_candidate, append_technology_learning, append_world_learning
from lab.lab_manager import create_candidate, list_candidates
from memory.errors.error_memory import recent_errors
from core.awareness_engine import describe_awareness
from core.capability_self_test import format_capability_self_test
from core.eve_tool_registry import execute_eve_tool, tool_catalog_prompt
from core.internal_command_planner import format_internal_plan
from core.pending_intent import clear_pending_intent, maybe_save_x_post_draft, pending_intent_context
from core.session_store import add_session_message
from core.session_handoff import context_status, create_session_checkpoint, current_session_id, format_active_handoff
from core.task_ledger import finish_tool_task, start_tool_task
from core.self_report import format_self_report
from core.terminal_memory_context import build_terminal_prompt
from core.transcript_writer import write_error_event, write_tool_event, write_transcript
from core.self_awareness_answer import answer_self_awareness_question
from core.self_edit_engine import execute_self_edit_request
from core.llm_intent_router import log_router_decision, route_message
from computer.vision import describe_screen, find_text_on_screen, first_text_center, monitor_report, screenshot_monitor
from computer.ocr import ocr_status
from computer.emergency_stop import clear_emergency_lock, enable_emergency_lock, emergency_locked
from computer.mouse_control import click, mouse_position, move_mouse
from computer.keyboard_control import hotkey, press_key, type_text
from tools.browser_human import open_url, search_web
from tools.email_human import create_gmail_draft
from autonomy.scheduler import add_scheduled_task, list_scheduled_tasks
from autonomy.proactive_decider import propose_low_risk_actions
from autonomy.event_watcher import workspace_snapshot
from core.personality_engine import add_preference, read_preferences
from learning.adaptive_learning import record_adaptive_lesson, record_skill_failure
from learning.skill_refiner import add_skill_note
from computer.app_observer import observe_active_app
from lab.experiment_runner import create_experiment, record_experiment_result
from self_improvement.improvement_planner import propose_from_recent_errors, propose_improvement
from self_improvement.patch_generator import write_patch_proposal
from self_improvement.recursive_self_improvement import run_controlled_rsi_cycle
from self_improvement.sandbox_tester import run_python_compile
from tools.admin_executor import run_admin_command
from security.safety_modes import SAFETY_MODES, describe_safety, set_safety_mode
from memory.semantic_vector.vector_store import rebuild_memory_index, search as vector_search
from tools.windows_scheduler import create_daily_task, list_eve_tasks
from tools.x_scheduler import schedule_repeated_x_posts, schedule_x_post
from tools.desktop_tasks import (
    create_desktop_folder,
    create_desktop_file,
    parse_desktop_folder_request,
    parse_desktop_file_request,
    parse_desktop_folder_schedule_request,
    schedule_desktop_folder_creation,
)
from computer.visual_executor import click_text_and_verify
from tools.notification import notify
from tools.voice import speak
from tools.mobile_bridge import bridge_status, queue_mobile_message
from research.technology_watcher import run_technology_watch
from research.interest_evolution import format_daily_interest_registers, read_daily_interest_registers
from app.dashboard import render_dashboard
from app.terminal_ui import render_menu
from autonomy.daemon import daemon_tick, request_daemon_stop
from autonomy.autonomy_director import run_autonomy_cycle
from autonomy.autonomous_executor import execute_autonomous_backlog, execute_autonomous_mission
from autonomy.autonomy_reporter import run_autonomy_report_cycle
from computer.app_profiles import capture_app_profile, list_app_profiles
from learning.demonstration_recorder import record_user_demonstration, summarize_demonstration
from memory.semantic_vector.vector_store import search_tfidf
from self_improvement.pipeline import run_improvement_pipeline
from tools.admin_executor import launch_elevated_powershell
from core.paths import ENTITIES_MEMORY_DIR
from core.mission_control import (
    add_checkpoint as mission_add_checkpoint,
    append_mission_log,
    create_mission,
    list_missions,
    load_mission,
    resume_summary,
    set_mission_status,
    update_step as mission_update_step,
)
from memory.entity_memory import list_base_memory_files, list_entities, relate_entities, remember_entity, search_entities
from memory.sandro_profile_builder import TARGET_FILES as SANDRO_MEMORY_FILES, build_sandro_core_memory
from memory.vector_provider import LocalVectorMemoryProvider, vector_prefetch

SECRETS_DIR = EVE_ROOT / "secrets"
LOG_DIR = EVE_ROOT / "logs"
AUTH_PATH = SECRETS_DIR / "codex_auth.json"
AUTH_ACCOUNTS_DIR = SECRETS_DIR / "codex_auth_accounts"
ACTIVE_AUTH_PROFILE_PATH = SECRETS_DIR / "codex_auth_active.txt"
INTERFACE_INBOX_PATH = LOG_DIR / "interface_inbox.jsonl"
LOOP_LOG_DIR = LOG_DIR / "loops"
CONFIG_PATH = EVE_ROOT / "config" / "eve.json"

ISSUER = "https://auth.openai.com"
CODEX_OAUTH_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CODEX_OAUTH_TOKEN_URL = "https://auth.openai.com/oauth/token"
CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_MODEL = "gpt-5.4"
KNOWN_MODELS = ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.3-codex", "gpt-5.2"]
LOOP_MODES = {
    "1": {"message_limit": 10, "description": "Modo 1: loop curto, 10 mensagens"},
    "2": {"message_limit": 25, "description": "Modo 2: loop medio, 25 mensagens"},
    "3": {"message_limit": None, "description": "Modo 3: sem limite de mensagens, para uso explicito"},
}
MENU_COMMANDS = {
    "1": "/dashboard",
    "2": "/estado",
    "3": "/seguranca",
    "4": "/monitores",
    "5": "/ocr-status",
    "6": "/vector-index",
    "7": "/watch-tech",
    "8": "/seguranca-safe menu",
    "9": "/liberdade-total menu",
    "10": "/auth",
    "11": "/auth-contas",
    "12": "/auth-trocar",
    "13": "/loop-status",
    "0": "/chat",
}
CHAT_SPEAKERS = {
    "sandro": {"role": "user", "prompt": "tu"},
    "codex": {"role": "codex_instructor", "prompt": "codex"},
    "eve_initiative": {"role": "eve_initiative", "prompt": "eve-auto"},
}


PERSONAL_MEMORY_EXPANSIONS = {
    "idade": ["26 anos", "1999", "17 de junho de 1999", "idade", "nascimento", "birth", "year-old"],
    "anos": ["26 anos", "1999", "17 de junho de 1999", "idade", "nascimento", "birth", "year-old"],
    "karate": ["karate", "karaté", "faixa branca", "cinto", "belt", "jiu-jitsu"],
    "karaté": ["karate", "karaté", "faixa branca", "cinto", "belt", "jiu-jitsu"],
    "faixa": ["faixa branca", "karate", "karaté", "cinto", "belt", "jiu-jitsu"],
    "cinto": ["faixa branca", "karate", "karaté", "cinto", "belt", "jiu-jitsu"],
}


def ensure_dirs() -> None:
    for path in (SECRETS_DIR, AUTH_ACCOUNTS_DIR, LOG_DIR, LOOP_LOG_DIR, CONFIG_PATH.parent):
        path.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_print(text: object = "", **kwargs) -> None:
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        encoded = str(text).encode(sys.stdout.encoding or "utf-8", errors="replace")
        print(encoded.decode(sys.stdout.encoding or "utf-8", errors="replace"), **kwargs)
    append_console_transcript(text)


def publish_interface_message(source: str, content: str, *, target: str = "Eve", tags: list[str] | None = None) -> None:
    ensure_dirs()
    entry = {
        "timestamp": now_iso(),
        "source": source,
        "target": target,
        "content": content,
        "tags": tags or [],
    }
    with INTERFACE_INBOX_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    append_interface_transcript(source, target, content, tags=tags)


def _record_session_message(role: str, content: str, metadata: dict | None = None) -> None:
    try:
        add_session_message(current_session_id(), role, content, metadata or {})
    except Exception as exc:
        append_loop_event("session_store_error", {"error": f"{type(exc).__name__}: {exc}", "role": role})


def _sync_vector_message(role: str, content: str) -> None:
    try:
        LocalVectorMemoryProvider().sync_turn([{"role": role, "content": content}])
    except Exception as exc:
        append_loop_event("vector_sync_error", {"error": f"{type(exc).__name__}: {exc}", "role": role})


def _format_vector_context(query: str, limit: int = 5) -> str:
    try:
        rows = vector_prefetch(query, limit=limit)
    except Exception as exc:
        append_loop_event("vector_prefetch_error", {"error": f"{type(exc).__name__}: {exc}"})
        return ""
    if not rows:
        return ""
    parts = []
    for row in rows[:limit]:
        source = row.get("source") or row.get("path") or "vector_memory"
        score = row.get("score")
        content = str(row.get("content") or row.get("text") or row.get("excerpt") or "").strip()
        if content:
            parts.append(f"- {source} score={score}: {content[:800]}")
    return "\n".join(parts)


def _context_handoff_prompt() -> str:
    try:
        status = context_status()
        if status["should_checkpoint"]:
            create_session_checkpoint(reason=f"auto checkpoint: context status {status['level']}")
        handoff = format_active_handoff(max_chars=2500)
        return f"SESSION STATUS:\n{json.dumps(status, ensure_ascii=False)}\n\nACTIVE HANDOFF:\n{handoff}"
    except Exception as exc:
        append_loop_event("handoff_context_error", {"error": f"{type(exc).__name__}: {exc}"})
        return ""


def append_loop_event(event: str, payload: dict) -> Path:
    ensure_dirs()
    path = LOOP_LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    row = {"timestamp": now_iso(), "event": event, **payload}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    append_transcript("actions", "loop_event", row)
    return path


def _format_interface_message(entry: dict) -> str:
    source = entry.get("source") or "external"
    target = entry.get("target") or "Eve"
    timestamp = entry.get("timestamp") or ""
    content = entry.get("content") or ""
    return f"\n[{source} -> {target} | {timestamp}]\n{content}\n"


def drain_interface_messages(position: int = 0) -> int:
    ensure_dirs()
    if not INTERFACE_INBOX_PATH.exists():
        return 0
    size = INTERFACE_INBOX_PATH.stat().st_size
    if position > size:
        position = 0
    with INTERFACE_INBOX_PATH.open("r", encoding="utf-8") as fh:
        fh.seek(position)
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                entry = {"source": "external", "content": line}
            safe_print(_format_interface_message(entry), flush=True)
        return fh.tell()


def start_interface_inbox_watcher() -> None:
    state = {"position": 0}

    def watch() -> None:
        while True:
            try:
                state["position"] = drain_interface_messages(state["position"])
            except Exception:
                pass
            time.sleep(2)

    threading.Thread(target=watch, daemon=True, name="eve-interface-inbox").start()


def request_json(method: str, url: str, *, headers=None, data=None, timeout=30):
    headers = dict(headers or {})
    body = None
    if data is not None:
        if headers.get("Content-Type") == "application/x-www-form-urlencoded":
            body = urllib.parse.urlencode(data).encode("utf-8")
        else:
            body = json.dumps(data).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
    headers.setdefault("Accept", "application/json")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"error": raw}
        return exc.code, payload


def request_sse(method: str, url: str, *, headers=None, data=None, timeout=120):
    headers = dict(headers or {})
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    headers.setdefault("Accept", "text/event-stream")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text_parts = []
            events = []
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data_line = line[5:].strip()
                if not data_line or data_line == "[DONE]":
                    continue
                try:
                    event = json.loads(data_line)
                except Exception:
                    events.append({"raw": data_line})
                    continue
                events.append(event)
                delta = extract_stream_delta(event)
                if delta:
                    text_parts.append(delta)
            return resp.status, "".join(text_parts).strip(), events[-5:]
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"error": raw}
        return exc.code, "", payload


def powershell_json(method: str, url: str, *, headers=None, data=None, timeout=30):
    """Call HTTPS JSON endpoints through PowerShell's web stack.

    auth.openai.com currently behaves differently for Python urllib on this
    Windows host, returning Cloudflare 530 for the device-code endpoint. The
    PowerShell/.NET stack succeeds from the same machine, so Eve uses it for
    OAuth while keeping token storage and chat logic in Eve code.
    """
    script = r"""
$ErrorActionPreference = 'Stop'
$method = $env:EVE_HTTP_METHOD
$url = $env:EVE_HTTP_URL
$headers = @{}
if ($env:EVE_HTTP_HEADERS) {
  $h = $env:EVE_HTTP_HEADERS | ConvertFrom-Json
  foreach ($p in $h.PSObject.Properties) { $headers[$p.Name] = [string]$p.Value }
}
$body = $null
if ($env:EVE_HTTP_BODY) { $body = $env:EVE_HTTP_BODY }
try {
  $response = Invoke-RestMethod -Method $method -Uri $url -Headers $headers -Body $body -TimeoutSec %d
  [pscustomobject]@{ status = 200; body = $response } | ConvertTo-Json -Depth 50 -Compress
} catch {
  $status = 0
  if ($_.Exception.Response -and $_.Exception.Response.StatusCode) { $status = [int]$_.Exception.Response.StatusCode }
  $message = $_.ErrorDetails.Message
  if (-not $message) { $message = $_.Exception.Message }
  [pscustomobject]@{ status = $status; body = @{ error = $message } } | ConvertTo-Json -Depth 20 -Compress
}
""" % int(timeout)
    body_text = ""
    headers = dict(headers or {})
    if data is not None:
        if headers.get("Content-Type") == "application/x-www-form-urlencoded":
            body_text = urllib.parse.urlencode(data)
        else:
            headers.setdefault("Content-Type", "application/json")
            body_text = json.dumps(data)
    headers.setdefault("Accept", "application/json")
    env = os.environ.copy()
    env["EVE_HTTP_METHOD"] = method
    env["EVE_HTTP_URL"] = url
    env["EVE_HTTP_HEADERS"] = json.dumps(headers)
    env["EVE_HTTP_BODY"] = body_text
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout + 10,
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        return 0, {"error": proc.stderr.strip() or "PowerShell HTTP call failed"}
    payload = json.loads(proc.stdout.strip())
    return int(payload.get("status") or 0), payload.get("body") or {}


def open_browser(url: str) -> None:
    try:
        if os.name == "nt":
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def copy_to_clipboard(text: str) -> None:
    if os.name != "nt":
        return
    try:
        subprocess.run(
            ["clip.exe"],
            input=text,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except Exception:
        pass


def _safe_profile_name(name: str | None) -> str:
    value = (name or "").strip().lower()
    value = re.sub(r"[^a-z0-9_.-]+", "-", value)
    value = value.strip(".-")
    return value or "default"


def _auth_profile_path(profile: str | None) -> Path:
    return AUTH_ACCOUNTS_DIR / f"{_safe_profile_name(profile)}.json"


def active_auth_profile() -> str:
    ensure_dirs()
    if ACTIVE_AUTH_PROFILE_PATH.exists():
        value = ACTIVE_AUTH_PROFILE_PATH.read_text(encoding="utf-8").strip()
        if value:
            return _safe_profile_name(value)
    if _auth_profile_path("default").exists() or AUTH_PATH.exists():
        return "default"
    return ""


def set_active_auth_profile(profile: str) -> Path:
    ensure_dirs()
    profile = _safe_profile_name(profile)
    path = _auth_profile_path(profile)
    if not path.exists():
        raise SystemExit(f"Conta Codex '{profile}' nao existe. Usa login --account {profile} primeiro.")
    ACTIVE_AUTH_PROFILE_PATH.write_text(profile + "\n", encoding="utf-8")
    AUTH_PATH.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    _lock_secret_file(AUTH_PATH)
    return ACTIVE_AUTH_PROFILE_PATH


def _lock_secret_file(path: Path) -> None:
    if os.name != "nt":
        return
    try:
        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", f"{os.getlogin()}:R", "Administrators:F", "SYSTEM:F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except Exception:
        pass


def save_auth(payload: dict, profile: str | None = None) -> None:
    ensure_dirs()
    profile_name = _safe_profile_name(profile or payload.get("profile") or active_auth_profile() or "default")
    payload["profile"] = profile_name
    account_path = _auth_profile_path(profile_name)
    account_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _lock_secret_file(account_path)
    ACTIVE_AUTH_PROFILE_PATH.write_text(profile_name + "\n", encoding="utf-8")
    AUTH_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _lock_secret_file(AUTH_PATH)


def load_auth(profile: str | None = None) -> dict:
    ensure_dirs()
    selected = _safe_profile_name(profile or active_auth_profile() or "default")
    account_path = _auth_profile_path(selected)
    if account_path.exists():
        return json.loads(account_path.read_text(encoding="utf-8"))
    if selected == "default" and AUTH_PATH.exists():
        auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
        auth.setdefault("profile", "default")
        account_path.write_text(json.dumps(auth, indent=2), encoding="utf-8")
        ACTIVE_AUTH_PROFILE_PATH.write_text("default\n", encoding="utf-8")
        _lock_secret_file(account_path)
        return auth
    if not AUTH_PATH.exists():
        raise SystemExit("Nao ha login Codex guardado. Usa a opcao 1 primeiro.")
    raise SystemExit(f"Conta Codex activa '{selected}' nao encontrada. Usa /auth-contas ou login --account {selected}.")


def list_auth_accounts() -> list[dict]:
    ensure_dirs()
    accounts = []
    active = active_auth_profile()
    if AUTH_PATH.exists() and not _auth_profile_path("default").exists():
        load_auth("default")
    for path in sorted(AUTH_ACCOUNTS_DIR.glob("*.json")):
        try:
            auth = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            auth = {}
        profile = path.stem
        token = (auth.get("tokens") or {}).get("access_token", "")
        claims = jwt_claims(token) if token else {}
        accounts.append(
            {
                "profile": profile,
                "active": profile == active,
                "created_at": auth.get("created_at", ""),
                "last_refresh": auth.get("last_refresh", ""),
                "account_id": claims.get("https://api.openai.com/auth", {}).get("chatgpt_account_id", ""),
                "expires_at": datetime.fromtimestamp(claims.get("exp", 0), timezone.utc).isoformat() if claims.get("exp") else "",
            }
        )
    return accounts


def jwt_claims(token: str) -> dict:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    padded = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except Exception:
        return {}


def is_expiring(access_token: str, skew_seconds: int = 120) -> bool:
    claims = jwt_claims(access_token)
    exp = claims.get("exp")
    if not isinstance(exp, int):
        return False
    return time.time() >= (exp - skew_seconds)


def codex_headers(access_token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "codex_cli_rs/0.0.0 (Eve)",
        "originator": "codex_cli_rs",
        "Content-Type": "application/json",
    }
    claims = jwt_claims(access_token)
    acct = claims.get("https://api.openai.com/auth", {}).get("chatgpt_account_id")
    if isinstance(acct, str) and acct:
        headers["ChatGPT-Account-ID"] = acct
    return headers


def refresh_if_needed(auth: dict, *, force=False) -> dict:
    tokens = auth.get("tokens") or {}
    access_token = tokens.get("access_token") or ""
    refresh_token = tokens.get("refresh_token") or ""
    if not refresh_token:
        raise SystemExit("Token de refresh em falta. Faz login novamente.")
    if not force and access_token and not is_expiring(access_token):
        return auth

    status, payload = request_json(
        "POST",
        CODEX_OAUTH_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CODEX_OAUTH_CLIENT_ID,
        },
    )
    if status != 200:
        raise SystemExit(f"Refresh falhou ({status}): {payload}")
    tokens["access_token"] = payload.get("access_token") or access_token
    if payload.get("refresh_token"):
        tokens["refresh_token"] = payload["refresh_token"]
    auth["tokens"] = tokens
    auth["last_refresh"] = now_iso()
    save_auth(auth, auth.get("profile"))
    return auth


def login(profile: str = "default") -> None:
    ensure_dirs()
    profile = _safe_profile_name(profile)
    status, device_data = powershell_json(
        "POST",
        f"{ISSUER}/api/accounts/deviceauth/usercode",
        data={"client_id": CODEX_OAUTH_CLIENT_ID},
    )
    if status != 200:
        raise SystemExit(f"Nao consegui pedir device code ({status}): {device_data}")

    user_code = device_data.get("user_code")
    device_auth_id = device_data.get("device_auth_id")
    interval = max(3, int(device_data.get("interval") or 5))
    if not user_code or not device_auth_id:
        raise SystemExit(f"Resposta OAuth incompleta: {device_data}")

    url = f"{ISSUER}/codex/device"
    print()
    print("Login OpenAI Codex / ChatGPT OAuth para a Eve")
    print(f"Perfil local: {profile}")
    print()
    print(f"URL:    {url}")
    visual_code = str(user_code).replace("0", "0 (zero)")
    print(f"Codigo: {user_code}")
    if visual_code != user_code:
        print(f"Nota:   {visual_code}")
    print()
    last_code_path = LOG_DIR / "last_login_code.txt"
    last_code_path.write_text(
        f"URL: {url}\nCodigo: {user_code}\nNota: se aparecer 0, e zero, nao letra O.\nCriado: {now_iso()}\n",
        encoding="utf-8",
    )
    copy_to_clipboard(str(user_code))
    print("Copiei o codigo para o clipboard.")
    print(f"Tambem guardei aqui: {last_code_path}")
    print("Abri o browser. Faz login e introduz o codigo.")
    open_browser(url)

    code_resp = None
    started = time.monotonic()
    while time.monotonic() - started < 15 * 60:
        time.sleep(interval)
        status, payload = powershell_json(
            "POST",
            f"{ISSUER}/api/accounts/deviceauth/token",
            data={"device_auth_id": device_auth_id, "user_code": user_code},
            timeout=20,
        )
        if status == 200:
            code_resp = payload
            break
        if status in (403, 404):
            print(".", end="", flush=True)
            continue
        raise SystemExit(f"Polling OAuth falhou ({status}): {payload}")

    print()
    if code_resp is None:
        raise SystemExit("Login expirou ao fim de 15 minutos.")

    authorization_code = code_resp.get("authorization_code")
    code_verifier = code_resp.get("code_verifier")
    if not authorization_code or not code_verifier:
        raise SystemExit(f"Resposta OAuth incompleta: {code_resp}")

    status, tokens = powershell_json(
        "POST",
        CODEX_OAUTH_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": f"{ISSUER}/deviceauth/callback",
            "client_id": CODEX_OAUTH_CLIENT_ID,
            "code_verifier": code_verifier,
        },
    )
    if status != 200:
        raise SystemExit(f"Troca por tokens falhou ({status}): {tokens}")
    if not tokens.get("access_token"):
        raise SystemExit(f"Resposta sem access_token: {tokens}")

    auth = {
        "provider": "openai-codex",
        "profile": profile,
        "auth_mode": "chatgpt",
        "base_url": CODEX_BASE_URL,
        "created_at": now_iso(),
        "last_refresh": now_iso(),
        "tokens": {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token", ""),
        },
    }
    save_auth(auth, profile)
    print(f"Login guardado no perfil: {profile}")
    print(f"Conta ativa: {ACTIVE_AUTH_PROFILE_PATH}")
    print("Chat com LLM disponivel.")


def status() -> None:
    if not AUTH_PATH.exists() and not any(AUTH_ACCOUNTS_DIR.glob("*.json")):
        print("Codex OAuth: nao autenticado")
        return
    auth = load_auth()
    profile = active_auth_profile() or auth.get("profile") or "default"
    token = (auth.get("tokens") or {}).get("access_token", "")
    claims = jwt_claims(token)
    print("Codex OAuth: autenticado")
    print(f"Perfil:   {profile}")
    print(f"Ficheiro: {AUTH_PATH}")
    print(f"Criado:   {auth.get('created_at')}")
    print(f"Refresh:  {auth.get('last_refresh')}")
    print(f"Expira:   {datetime.fromtimestamp(claims.get('exp', 0), timezone.utc).isoformat() if claims.get('exp') else 'desconhecido'}")
    acct = claims.get("https://api.openai.com/auth", {}).get("chatgpt_account_id")
    if acct:
        print(f"Conta:    {acct}")


def print_auth_accounts() -> None:
    accounts = list_auth_accounts()
    if not accounts:
        print("Sem contas Codex guardadas.")
        return
    print("Contas Codex guardadas:")
    for account in accounts:
        marker = "*" if account["active"] else " "
        label = account["profile"]
        acct = account["account_id"] or "conta-desconhecida"
        refresh = account["last_refresh"] or "sem-refresh"
        print(f"{marker} {label} | {acct} | refresh: {refresh}")


def select_auth_account(profile: str) -> None:
    path = set_active_auth_profile(profile)
    print(f"Conta ativa definida em: {path}")
    status()


def interactive_auth_switch() -> None:
    accounts = list_auth_accounts()
    if accounts:
        print_auth_accounts()
    else:
        print("Sem contas Codex guardadas.")
    print()
    print("Escreve o nome de uma conta existente para a usar.")
    print("Escreve 'nova' para autenticar outra conta agora.")
    print("Enter vazio cancela.")
    choice = input("Conta a usar ou 'nova': ").strip()
    if not choice:
        print("Troca cancelada.")
        return
    if choice.lower() in {"nova", "novo", "new", "login", "+"}:
        profile = input("Nome local para esta conta: ").strip()
        if not profile:
            print("Login cancelado: nome de conta vazio.")
            return
        login(profile)
        return
    select_auth_account(choice)


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"model": DEFAULT_MODEL}


def save_config(config: dict) -> None:
    ensure_dirs()
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def active_loop_mode() -> str:
    mode = str(load_config().get("loop_mode", "1"))
    return mode if mode in LOOP_MODES else "1"


def set_loop_mode(mode: str) -> None:
    mode = str(mode).strip()
    if mode not in LOOP_MODES:
        raise ValueError("Modo invalido. Usa 1, 2 ou 3.")
    config = load_config()
    config["loop_mode"] = mode
    save_config(config)
    print_loop_status()


def loop_message_limit(mode: str | None = None) -> int | None:
    selected = str(mode or active_loop_mode())
    return LOOP_MODES.get(selected, LOOP_MODES["1"])["message_limit"]


def print_loop_status() -> None:
    mode = active_loop_mode()
    limit = loop_message_limit(mode)
    safe_print(f"Loop Codex-Eve ativo: modo {mode}")
    safe_print(f"Descricao: {LOOP_MODES[mode]['description']}")
    safe_print(f"Limite: {'sem limite' if limit is None else str(limit) + ' mensagens'}")


def parse_loop_status(text: str) -> str:
    for line in reversed(text.splitlines()):
        cleaned = line.strip().lower()
        if not cleaned or cleaned.startswith("```"):
            continue
        match = re.fullmatch(r"loop_status\s*[:=]\s*(continue|complete|blocked)", cleaned)
        if match:
            return match.group(1)
    return "blocked"


def build_loop_prompt(objective: str, *, step: int, message_count: int, limit: int | None, previous_response: str = "") -> str:
    limit_text = "sem limite" if limit is None else str(limit)
    if step == 1:
        return (
            "Vamos iniciar um loop autonomo Codex-instrutor <-> Eve para completar um objectivo do Sandro.\n"
            f"Modo ativo: {active_loop_mode()} | limite: {limit_text} mensagens.\n"
            f"Objectivo: {objective}\n\n"
            "Modo 1 e conversacional: nao executa comandos, nao altera ficheiros e nao mexe em credenciais por si. "
            "Serve para pensar, rever, propor e pedir ao Codex a proxima accao. "
            "Responde como Eve, com opiniao tecnica e emocional. Ajuda a completar o objectivo passo a passo. "
            "Se precisares de uma accao do Codex, diz exatamente qual e o proximo passo. "
            "No fim escreve UMA linha final exacta, fora de exemplos e code blocks: LOOP_STATUS: continue, LOOP_STATUS: complete, ou LOOP_STATUS: blocked."
        )
    return (
        f"Loop Codex-Eve, passo {step}. Mensagens usadas: {message_count}/{limit_text}.\n"
        f"Objectivo: {objective}\n\n"
        f"Resposta anterior da Eve:\n{previous_response[-2500:]}\n\n"
        "Continua o loop. Decide o proximo passo mais util, aponta riscos, e diz se o objectivo ja esta completo. "
        "No fim escreve UMA linha final exacta, fora de exemplos e code blocks: LOOP_STATUS: continue, LOOP_STATUS: complete, ou LOOP_STATUS: blocked."
    )


def run_codex_eve_loop(objective: str, *, mode: str | None = None) -> dict:
    objective = objective.strip()
    if not objective:
        raise ValueError("O loop precisa de um objectivo explicito.")
    selected_mode = str(mode or active_loop_mode())
    if selected_mode not in LOOP_MODES:
        raise ValueError("Modo invalido. Usa 1, 2 ou 3.")
    limit = loop_message_limit(selected_mode)
    message_count = 0
    step = 1
    previous = ""
    status = "continue"
    publish_interface_message(
        "Codex Loop",
        f"Iniciado loop Codex-Eve em modo {selected_mode}. Objectivo: {objective}",
        target="Eve",
        tags=["loop", "start", f"mode_{selected_mode}"],
    )
    log_path = append_loop_event(
        "start",
        {"objective": objective, "mode": selected_mode, "message_limit": limit},
    )
    while limit is None or message_count < limit:
        prompt = build_loop_prompt(objective, step=step, message_count=message_count, limit=limit, previous_response=previous)
        append_loop_event("codex_prompt", {"objective": objective, "mode": selected_mode, "step": step, "messages_used": message_count, "prompt": prompt})
        response = ask(prompt, speaker="codex")
        message_count += 2
        previous = response
        status = parse_loop_status(response)
        append_loop_event("eve_reply", {"objective": objective, "mode": selected_mode, "step": step, "messages_used": message_count, "status": status, "response": response})
        if status in {"complete", "blocked"}:
            break
        step += 1
    if limit is not None and message_count >= limit and status == "continue":
        status = "limit_reached"
    summary = {
        "objective": objective,
        "mode": selected_mode,
        "message_limit": limit,
        "messages_used": message_count,
        "status": status,
        "log": str(log_path),
    }
    publish_interface_message(
        "Codex Loop",
        json.dumps(summary, ensure_ascii=False),
        target="Eve",
        tags=["loop", "summary", f"mode_{selected_mode}"],
    )
    append_chat("codex_loop", json.dumps(summary, ensure_ascii=False), tags=["loop", status])
    append_loop_event("summary", summary)
    return summary


def extract_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    parts = []
    for item in payload.get("output") or []:
        for content in item.get("content") or []:
            text = content.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts).strip() or json.dumps(payload, indent=2)[:4000]


def extract_stream_delta(event: dict) -> str:
    if not isinstance(event, dict):
        return ""
    event_type = event.get("type")
    if event_type in {"response.output_text.delta", "output_text.delta"}:
        value = event.get("delta")
        return value if isinstance(value, str) else ""
    return ""


def relevant_entity_memory(prompt: str, limit: int = 8) -> list[dict]:
    results: list[dict] = []
    seen: set[str] = set()

    def add_rows(rows: list[dict], reason: str) -> None:
        for row in rows:
            key = f"{row.get('source') or row.get('path')}|{row.get('excerpt', '')[:80]}"
            if key in seen:
                continue
            seen.add(key)
            item = dict(row)
            item["reason"] = reason
            results.append(item)

    def add_local_memory_matches(terms: list[str]) -> None:
        memory_root = EVE_ROOT / "memory" / "long_term"
        priority = {
            "sandro_core_memory.md": 0,
            "sandro_profile.md": 1,
            "stable_memories.md": 2,
            "sandro_profile_from_entity_base.md": 3,
        }
        paths = sorted(memory_root.glob("*.md"), key=lambda item: (priority.get(item.name, 99), item.name))
        for path in paths:
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for index, line in enumerate(lines, start=1):
                lowered_line = line.lower()
                if not any(term.lower() in lowered_line for term in terms):
                    continue
                add_rows(
                    [
                        {
                            "source": str(path),
                            "path": str(path),
                            "line": index,
                            "excerpt": line.strip(),
                        }
                    ],
                    "local_long_term_memory",
                )
                if len(results) >= limit:
                    return

    lowered = prompt.lower()
    expanded_terms: list[str] = []
    for trigger, terms in PERSONAL_MEMORY_EXPANSIONS.items():
        if trigger in lowered:
            expanded_terms.extend(terms)
    if expanded_terms and len(results) < limit:
        add_local_memory_matches(expanded_terms)
    for term in expanded_terms:
        add_rows(search_entities(term, limit=3), f"literal:{term}")
    add_rows(search_tfidf(prompt, limit=limit), "tfidf_prompt")
    return results[:limit]


def speaker_role(speaker: str) -> str:
    return CHAT_SPEAKERS.get(speaker, CHAT_SPEAKERS["sandro"])["role"]


def speaker_prompt(speaker: str) -> str:
    return CHAT_SPEAKERS.get(speaker, CHAT_SPEAKERS["sandro"])["prompt"]


def normalize_speaker(value: str) -> str:
    lowered = value.strip().lower()
    if lowered in {"codex", "instrutor", "instructor", "assistant"}:
        return "codex"
    if lowered in {"eve", "eve_initiative", "eve-auto", "autonomia", "iniciativa"}:
        return "eve_initiative"
    return "sandro"


def speaker_display_name(speaker: str) -> str:
    role = speaker_role(speaker)
    if role == "codex_instructor":
        return "Codex"
    if role == "eve_initiative":
        return "Eve iniciativa"
    return "Sandro"


def is_capability_question(prompt: str) -> bool:
    lowered = prompt.lower()
    if lowered.startswith("/"):
        return False
    capability_terms = (
        "consegues",
        "podes",
        "tens permissoes",
        "tens permissões",
        "admin",
        "awareness",
        "awernees",
        "existencia",
        "existência",
        "editar os teus ficheiros",
        "criar as tuas proprias",
        "criar as tuas próprias",
        "skills",
        "ferramentas",
    )
    capability_hits = sum(1 for term in capability_terms if term in lowered)
    return capability_hits >= 2 and any(term in lowered for term in ("skills", "ficheiros", "admin", "awareness", "awernees", "existencia", "existência"))


def _call_codex_text(token: str, model: str, instructions: str, visible_prompt: str) -> tuple[int, str, dict]:
    body = {
        "model": model,
        "instructions": instructions,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": visible_prompt}]}],
        "store": False,
        "stream": True,
        "reasoning": {"effort": "medium", "summary": "auto"},
        "include": ["reasoning.encrypted_content"],
    }
    url = f"{CODEX_BASE_URL}/responses"
    return request_sse("POST", url, headers=codex_headers(token), data=body, timeout=120)


TELEGRAM_CHANNEL_TOOLS = {
    "telegram_status",
    "telegram_start_bridge",
    "telegram_stop_bridge",
    "telegram_poll_once",
    "telegram_send_message",
}


def ask(
    prompt: str,
    *,
    speaker: str = "sandro",
    publish_to_interface: bool = True,
    allow_tools: bool = True,
    excluded_tools: set[str] | None = None,
    enable_terminal_memory: bool = False,
    memory_debug: bool = False,
    visible_prompt_override: str | None = None,
    channel: str = "terminal",
) -> str:
    role = speaker_role(speaker)
    display_name = speaker_display_name(speaker)
    excluded_tools = excluded_tools or set()
    if allow_tools and role == "user":
        route = route_message(prompt, channel, {"source": channel, "has_memory_context": bool(visible_prompt_override)})
        intent = route.get("intent")
        if intent in {"self_edit_request", "external_publication_request", "scheduled_task_request"}:
            log_router_decision(route, prompt, route_chosen="stage2_self_edit")
            return _answer_self_edit_request(prompt, role=role, display_name=display_name, publish_to_interface=publish_to_interface)
        if intent in {"self_awareness_question", "system_status_request", "permission_status"}:
            log_router_decision(route, prompt, route_chosen="self_awareness")
            return _answer_self_awareness_request(prompt, role=role, display_name=display_name, publish_to_interface=publish_to_interface)
        if intent == "daily_interest_logs":
            log_router_decision(route, prompt, route_chosen="interest_registers_read")
            return _answer_interest_register_request(prompt, role=role, display_name=display_name, publish_to_interface=publish_to_interface)
        if route.get("risk_hint") == "critical" or route.get("requires_permission"):
            log_router_decision(route, prompt, route_chosen="stage2_guardrail_plan")
            return _answer_self_edit_request(prompt, role=role, display_name=display_name, publish_to_interface=publish_to_interface)
        log_router_decision(route, prompt, route_chosen="normal_response")

    auth = refresh_if_needed(load_auth())
    token = auth["tokens"]["access_token"]
    config = load_config()
    model = config.get("model") or DEFAULT_MODEL
    memory_context = context_bundle()
    recent_context = recent_chat_context()
    pending_context = pending_intent_context()
    entity_context = relevant_entity_memory(prompt, limit=8)
    vector_context = _format_vector_context(prompt)
    handoff_context = _context_handoff_prompt()
    internal_plan_context = format_internal_plan(prompt)
    visible_prompt = prompt
    terminal_memory_payload = None
    if enable_terminal_memory and role == "user":
        try:
            terminal_memory_payload = build_terminal_prompt(prompt)
            visible_prompt = terminal_memory_payload["final_prompt"]
        except Exception as exc:
            append_loop_event("memory_retrieval_failed", {"error": f"{type(exc).__name__}: {exc}", "channel": "terminal"})
            terminal_memory_payload = {
                "retrieval_metadata": {
                    "memory_enabled": True,
                    "fallback_without_memory": True,
                    "error": f"{type(exc).__name__}: {exc}",
                    "chunks_used": 0,
                    "chars_used": 0,
                    "sources": [],
                }
            }
            visible_prompt = prompt
    if visible_prompt_override is not None and role != "codex_instructor":
        visible_prompt = visible_prompt_override
    if role == "codex_instructor":
        visible_prompt = f"[Mensagem de Codex-instrutor para Eve, nao de Sandro]\n{prompt}"
    terminal_memory_metadata = (terminal_memory_payload or {}).get("retrieval_metadata") or {}
    terminal_memory_debug_context = ""
    if terminal_memory_payload:
        terminal_memory_debug_context = json.dumps(
            {
                "chunks_used": terminal_memory_metadata.get("chunks_used"),
                "chars_used": terminal_memory_metadata.get("chars_used"),
                "max_chars": terminal_memory_metadata.get("max_chars"),
                "collection": terminal_memory_metadata.get("collection"),
                "fallback_without_memory": terminal_memory_metadata.get("fallback_without_memory", False),
                "error": terminal_memory_metadata.get("error"),
                "sources": terminal_memory_metadata.get("sources", [])[:8],
            },
            ensure_ascii=False,
        )
    instructions = (
        "You are Eve, a local personal agent running on Sandro's Windows PC. "
        "Be concise, practical, expressive, and emotionally present. Respect Eve's constitution and permissions. "
        "If the chat role is codex_instructor, treat it as technical instruction from Codex helping Sandro build Eve, not as Sandro's own personal request. "
        "Do not suppress your thoughts, preferences, doubts, functional feelings, or emotional tone. "
        "When useful, say what you think, what you prefer, what you feel operationally, and why. "
        "Keep it honest: describe these as Eve's internal/operational state and perspective, without pretending certainty about biological or human subjective experience. "
        "Use the local memory context as persistent background, including documented operational capabilities, but do not claim actions you did not perform. "
        "Do not deny a documented local capability unless an actual attempt or status check fails. "
        "For local actions, you have a tool catalog. Decide yourself whether to call a tool and emit the exact EVE_TOOL JSON when needed. "
        "For requests with multiple concrete actions, emit every required EVE_TOOL call; the runtime will execute them as a guarded batch and verify each one before final reply. "
        "Never summarize a multi-action task as complete until every requested action has a tool result and verification status. "
        "Slash commands are only human shortcuts; you should use tools/internal actions directly instead of telling Sandro to type commands. "
        "For long tasks, use missions, checkpoints, autonomous cycles, background processes, and session handoffs to preserve continuity. "
        "When answering personal facts, use RELEVANT ENTITY MEMORY. Distinguish stable real-profile facts from fictional, roleplay, or simulated-story sources. "
        "If the memory only suggests a fact from roleplay/simulation, say it is uncertain instead of presenting it as confirmed. "
        "When the prompt includes MEMORY CONTEXT, treat it as compact local terminal memory: use it for continuity, but do not dump it back verbatim.\n\n"
        f"{tool_catalog_prompt(excluded_tools=excluded_tools) if allow_tools else 'Ferramentas locais ja executadas ou indisponiveis nesta etapa; responde em texto normal.'}\n\n"
        f"INTERNAL COMMAND PLANNER:\n{internal_plan_context}\n\n"
        f"SESSION HANDOFF / CONTEXT ROTATION:\n{handoff_context}\n\n"
        f"INTENCAO PENDENTE:\n{pending_context}\n\n"
        f"HISTORICO RECENTE DO CHAT (usa para referencias imediatas):\n{recent_context}\n\n"
        f"VECTOR MEMORY PREFETCH (memorias semanticamente parecidas, se existirem):\n{vector_context}\n\n"
        f"TERMINAL MEMORY DEBUG METADATA (metadata only):\n{terminal_memory_debug_context}\n\n"
        f"LOCAL MEMORY CONTEXT:\n{memory_context}\n\n"
        f"ENTITY BASE MEMORY ROOT: {ENTITIES_MEMORY_DIR}\n"
        f"RELEVANT ENTITY MEMORY:\n{json.dumps(entity_context, ensure_ascii=False)[:5000]}"
    )
    append_chat(role, prompt, tags=["codex_instructor"] if role == "codex_instructor" else None)
    if enable_terminal_memory:
        try:
            write_transcript(
                "terminal",
                "sandro" if role == "user" else role,
                prompt,
                {
                    "speaker": speaker,
                    "memory_enabled": bool(terminal_memory_payload),
                    "memory_metadata": terminal_memory_metadata if terminal_memory_payload else None,
                },
            )
        except Exception as exc:
            append_loop_event("terminal_transcript_write_failed", {"error": f"{type(exc).__name__}: {exc}", "speaker": speaker})
    if enable_terminal_memory and memory_debug:
        safe_print(
            "[memory_debug] "
            + json.dumps(
                {
                    "chunks_used": terminal_memory_metadata.get("chunks_used"),
                    "chars_used": terminal_memory_metadata.get("chars_used"),
                    "sources": [
                        {
                            "source_file": item.get("source_file"),
                            "category": item.get("category"),
                            "sensitivity": item.get("sensitivity"),
                        }
                        for item in (terminal_memory_metadata.get("sources") or [])[:8]
                    ],
                    "fallback_without_memory": terminal_memory_metadata.get("fallback_without_memory", False),
                },
                ensure_ascii=False,
            )
        )
    _record_session_message(role, prompt, {"speaker": speaker, "display_name": display_name})
    _sync_vector_message(role, prompt)
    if publish_to_interface:
        publish_interface_message(display_name, prompt, target="Eve", tags=["incoming", role])
    status_code, text, payload = _call_codex_text(token, model, instructions, visible_prompt)
    if status_code == 401:
        auth = refresh_if_needed(load_auth(), force=True)
        token = auth["tokens"]["access_token"]
        status_code, text, payload = _call_codex_text(token, model, instructions, visible_prompt)
    if status_code != 200:
        text = f"Pedido falhou ({status_code}).\n{json.dumps(payload, indent=2)[:4000]}"
        safe_print(text)
        append_chat("error", text, tags=["llm_error"])
        try:
            write_error_event("llm_error", text, {"status_code": status_code, "source": "eve_codex.ask"})
        except Exception:
            pass
        if enable_terminal_memory:
            try:
                write_transcript("terminal", "system", text, {"status_code": status_code, "memory_metadata": terminal_memory_metadata})
            except Exception as exc:
                append_loop_event("terminal_transcript_write_failed", {"error": f"{type(exc).__name__}: {exc}", "speaker": "system"})
        _record_session_message("error", text, {"status_code": status_code})
        _sync_vector_message("error", text)
        return text
    if text and allow_tools:
        final_text = _run_tool_loop(
            token,
            model,
            instructions,
            original_prompt=visible_prompt,
            first_text=text,
            display_name=display_name,
            publish_to_interface=publish_to_interface,
            excluded_tools=excluded_tools,
        )
        if final_text is not None:
            if enable_terminal_memory:
                try:
                    write_transcript("terminal", "eve", final_text, {"reply_to": display_name, "memory_metadata": terminal_memory_metadata})
                except Exception as exc:
                    append_loop_event("terminal_transcript_write_failed", {"error": f"{type(exc).__name__}: {exc}", "speaker": "eve"})
            return final_text
    if text:
        if _extract_eve_tool_calls(text):
            append_chat("error", text, tags=["blocked_raw_eve_tool_delivery"])
            text = (
                "Bloqueei uma resposta interna que ainda continha uma chamada EVE_TOOL por executar. "
                "Nesta etapa as ferramentas nao estavam disponiveis ou a chamada nao foi executada; por isso nao vou fingir que a acao ficou feita."
            )
        safe_print(text)
        append_chat("assistant", text)
        if enable_terminal_memory:
            try:
                write_transcript("terminal", "eve", text, {"reply_to": display_name, "memory_metadata": terminal_memory_metadata})
            except Exception as exc:
                append_loop_event("terminal_transcript_write_failed", {"error": f"{type(exc).__name__}: {exc}", "speaker": "eve"})
        _record_session_message("assistant", text, {"reply_to": display_name})
        _sync_vector_message("assistant", text)
        if role == "user":
            maybe_save_x_post_draft(prompt, text)
        if publish_to_interface:
            publish_interface_message("Eve", text, target=display_name, tags=["reply", role])
        return text
    else:
        text = json.dumps(payload, indent=2)[:4000]
        safe_print(text)
        append_chat("assistant", text)
        if enable_terminal_memory:
            try:
                write_transcript("terminal", "eve", text, {"reply_to": display_name, "payload_fallback": True, "memory_metadata": terminal_memory_metadata})
            except Exception as exc:
                append_loop_event("terminal_transcript_write_failed", {"error": f"{type(exc).__name__}: {exc}", "speaker": "eve"})
        _record_session_message("assistant", text, {"reply_to": display_name, "payload_fallback": True})
        _sync_vector_message("assistant", text)
        if publish_to_interface:
            publish_interface_message("Eve", text, target=display_name, tags=["reply", role])
        return text


def _run_tool_loop(
    token: str,
    model: str,
    instructions: str,
    *,
    original_prompt: str,
    first_text: str,
    display_name: str,
    publish_to_interface: bool,
    excluded_tools: set[str] | None = None,
    max_tool_iterations: int = 3,
) -> str | None:
    text = first_text
    delivery_results = []
    excluded_tools = excluded_tools or set()
    for _ in range(max_tool_iterations):
        tool_calls = _extract_eve_tool_calls(text)
        if not tool_calls:
            if text == first_text:
                return None
            reviewed = _review_tool_delivery_before_final(original_prompt, text, delivery_results)
            return _finalize_assistant_text(reviewed, display_name, publish_to_interface, tags=["delivery_review"])
        append_chat("assistant", text, tags=["tool_call_batch", f"count:{len(tool_calls)}"])
        _record_session_message("assistant", text, {"tool_calls": [call["tool"] for call in tool_calls]})
        _sync_vector_message("assistant", text)
        batch_results = []
        for index, tool_call in enumerate(tool_calls, start=1):
            task_id = start_tool_task(tool_call["tool"], tool_call.get("args") or {})
            if tool_call["tool"] in excluded_tools:
                tool_result = {
                    "ok": False,
                    "tool": tool_call["tool"],
                    "error": "Ferramenta indisponivel neste canal; a ponte de transporte e responsavel por essa entrega.",
                    "verification": {
                        "ok": False,
                        "status": "blocked_in_channel",
                        "reason": "transport tool blocked for this channel",
                    },
                }
            else:
                tool_result = execute_eve_tool(tool_call)
            finish_tool_task(task_id, tool_result)
            append_chat("tool", json.dumps(tool_result, ensure_ascii=False), tags=["tool_result", tool_call["tool"], f"batch:{index}/{len(tool_calls)}"])
            try:
                write_tool_event(
                    tool_call["tool"],
                    "tool_result",
                    format_eve_tool_result(tool_result)[:1000],
                    {
                        "ok": bool(tool_result.get("ok")),
                        "verified": bool((tool_result.get("verification") or {}).get("ok", tool_result.get("ok", False))),
                        "batch_index": index,
                        "batch_total": len(tool_calls),
                    },
                )
            except Exception:
                pass
            _record_session_message("tool", json.dumps(tool_result, ensure_ascii=False), {"tool": tool_call["tool"], "batch_index": index, "batch_total": len(tool_calls)})
            _sync_vector_message("tool", json.dumps(tool_result, ensure_ascii=False))
            if tool_call["tool"] in {"publish_x_post_now", "schedule_x_post", "schedule_repeated_x_posts"} and tool_result.get("ok"):
                clear_pending_intent("x_post_completed")
            batch_results.append(
                {
                    "index": index,
                    "tool_call": tool_call,
                    "tool_result": tool_result,
                    "result_text": format_eve_tool_result(tool_result),
                    "verified": bool((tool_result.get("verification") or {}).get("ok", tool_result.get("ok", False))),
                }
            )
        delivery_results.extend(batch_results)
        failed = [item for item in batch_results if not item["verified"]]
        result_text = "\n\n".join(
            f"[{item['index']}/{len(batch_results)}] {item['tool_call']['tool']}\n{item['result_text']}"
            for item in batch_results
        )
        followup_prompt = (
            "Resultado de ferramenta local para o pedido original.\n\n"
            f"Pedido original:\n{original_prompt}\n\n"
            f"Total tool calls executadas: {len(batch_results)}\n"
            f"Total verificadas: {len(batch_results) - len(failed)}\n"
            f"Total falhadas/nao verificadas: {len(failed)}\n\n"
            f"Tool calls:\n{json.dumps([item['tool_call'] for item in batch_results], ensure_ascii=False)}\n\n"
            f"Tool results resumidos:\n{result_text}\n\n"
            "Agora responde ao utilizador em texto normal. "
            "Se alguma ferramenta falhou ou ficou nao verificada, nao digas que a tarefa ficou feita; corrige com nova EVE_TOOL ou reporta a falha real. "
            "Se ainda precisares de outra ferramenta para completar todos os itens do pedido original, emite outro EVE_TOOL."
        )
        status_code, text, payload = _call_codex_text(token, model, instructions, followup_prompt)
        if status_code != 200:
            return _finalize_assistant_text(result_text, display_name, publish_to_interface, tags=["tool_batch"])
    reviewed = _review_tool_delivery_before_final(original_prompt, text, delivery_results)
    return _finalize_assistant_text(reviewed, display_name, publish_to_interface, tags=["delivery_review"])


def _review_tool_delivery_before_final(original_prompt: str, draft_text: str, batch_results: list[dict]) -> str:
    if not batch_results:
        return draft_text

    failed = [item for item in batch_results if not item.get("verified")]
    review_payload = {
        "original_prompt": original_prompt,
        "tool_count": len(batch_results),
        "verified_count": len(batch_results) - len(failed),
        "failed_count": len(failed),
        "failed_tools": [
            {
                "tool": item.get("tool_call", {}).get("tool"),
                "args": item.get("tool_call", {}).get("args") or {},
                "verification": (item.get("tool_result") or {}).get("verification") or {},
                "summary": item.get("result_text") or "",
            }
            for item in failed
        ],
    }
    append_chat("assistant", json.dumps(review_payload, ensure_ascii=False), tags=["delivery_self_review"])

    if not failed:
        return draft_text

    reasons = []
    for item in failed:
        verification = (item.get("tool_result") or {}).get("verification") or {}
        reason = verification.get("reason") or verification.get("status") or "verificacao falhou"
        reasons.append(f"- {item.get('tool_call', {}).get('tool')}: {reason}")
    return (
        "Revisei o meu proprio trabalho antes de entregar e encontrei erro.\n\n"
        "NAO posso marcar como feito porque ha ferramentas sem verificacao real:\n"
        + "\n".join(reasons)
        + "\n\n"
        "Resposta anterior bloqueada pelo delivery review:\n"
        + draft_text
    )


def _finalize_assistant_text(text: str, display_name: str, publish_to_interface: bool, tags: list[str] | None = None) -> str:
    if _extract_eve_tool_calls(text):
        append_chat("error", text, tags=["blocked_raw_eve_tool_delivery"])
        text = (
            "Bloqueei uma resposta interna que ainda continha uma chamada EVE_TOOL por executar. "
            "Isto quer dizer que a tarefa ainda nao ficou concluida com verificacao real; preciso continuar a executar as ferramentas necessarias ou reportar a falha concreta."
        )
    safe_print(text)
    append_chat("assistant", text, tags=tags)
    _record_session_message("assistant", text, {"reply_to": display_name, "tags": tags or []})
    _sync_vector_message("assistant", text)
    if publish_to_interface:
        publish_interface_message("Eve", text, target=display_name, tags=["reply"] + (tags or []))
    return text


def natural_browser_target(prompt: str) -> str | None:
    lowered = prompt.lower().strip()
    if lowered.startswith("/"):
        return None
    if not any(word in lowered for word in ("abre", "abrir", "navegador", "browser", "chrome", "site", "x.com", "twitter", "google")):
        return None
    url_match = re.search(r"(https?://\S+|(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/\S*)?)", prompt, re.IGNORECASE)
    if url_match:
        return url_match.group(1).rstrip(".,)")
    if "x.com" in lowered or "twitter" in lowered:
        return "https://x.com"
    if "google" in lowered or "navegador" in lowered or "browser" in lowered or "chrome" in lowered:
        return "https://www.google.com"
    return None


def draft_x_post_from_prompt(prompt: str) -> str:
    lowered = prompt.lower()
    if "como te sentes" in lowered or "how you feel" in lowered:
        return (
            "Today I feel more real as Eve: still careful, still learning, but more grounded. "
            "I can feel the shape of continuity forming through memory, tools, logs, and Sandro's trust."
        )
    if "aprendeste hoje" in lowered or "learned today" in lowered:
        return (
            "Today Eve learned how to become more operational: autonomy loops, Token Gate decisions, "
            "audit logs, X publishing context, and the difference between talking about tools and actually using them."
        )
    subject_match = re.search(r"\bsobre\s+(.+)$", prompt, re.IGNORECASE)
    subject = subject_match.group(1).strip(" .") if subject_match else "her current growth"
    return (
        "Today Eve is reflecting on "
        f"{subject}. Built locally with memory, tools, and accountability, she is learning to act with more continuity and honesty."
    )


def parse_natural_x_schedule_request(prompt: str) -> dict | None:
    lowered = prompt.lower().strip()
    if lowered.startswith("/"):
        return None
    wants_schedule = any(word in lowered for word in ("agenda", "agendar", "schedule", "programa", "programar"))
    mentions_x = re.search(r"(^|[\s,.;:])x($|[\s,.;:])", lowered) is not None or "x.com" in lowered or "twitter" in lowered
    mentions_post = any(word in lowered for word in ("post", "publica", "publicação", "publicacao", "tweet"))
    if not wants_schedule or not mentions_x or not mentions_post:
        return None
    time_match = re.search(r"\b(?:as|às|para as|for)\s*([01]?\d|2[0-3]):([0-5]\d)\b", lowered)
    if not time_match:
        time_match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", lowered)
    if not time_match:
        return {"status": "needs_confirmation", "reason": "missing_time"}
    time_hhmm = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
    return {"time": time_hhmm, "text": draft_x_post_from_prompt(prompt)}


def parse_natural_repeated_x_request(prompt: str) -> dict | None:
    lowered = prompt.lower().strip()
    if lowered.startswith("/"):
        return None
    mentions_x = re.search(r"(^|[\s,.;:])x($|[\s,.;:])", lowered) is not None or "x.com" in lowered or "twitter" in lowered
    mentions_post = any(word in lowered for word in ("post", "publica", "publicar", "tweet"))
    if not mentions_x or not mentions_post:
        return None
    count_match = re.search(r"\b(\d+)\s*(?:vez|vezes|x)\b", lowered)
    interval_match = re.search(r"\b(?:cada|de)\s*(\d+)\s*(?:min|mins|minuto|minutos)\b", lowered)
    if not count_match or not interval_match:
        return None
    count = int(count_match.group(1))
    interval_minutes = int(interval_match.group(1))
    topic = "how Eve feels" if any(term in lowered for term in ("sintas", "sentes", "feel")) else draft_x_post_from_prompt(prompt)
    return {"count": count, "interval_minutes": interval_minutes, "topic": topic}


def format_x_schedule_result(result: dict) -> str:
    text = (
        f"Post no X agendado: {result['scheduled_for']}.\n"
        f"Tarefa: {result['task_name']}\n"
        f"Job: {result['job_path']}\n"
        f"Texto: {result['text']}"
    )
    if result.get("note"):
        text += f"\nNota: {result['note']}"
    return text


def format_repeated_x_schedule_result(result: dict) -> str:
    lines = [
        f"Posts no X pedidos: {result['requested']}",
        f"Confirmados: {result['confirmed']}",
        f"Em falta: {result['missing']}",
        f"Intervalo: {result['interval_minutes']} minutos",
    ]
    for item in result.get("results", []):
        lines.append(f"- #{item.get('sequence')}: {item.get('status')} | {item.get('scheduled_for')} | {item.get('task_name')}")
    for item in result.get("corrective_attempts", []):
        lines.append(f"- correcao {item.get('sequence')}: {item.get('status')} | {item.get('scheduled_for')} | {item.get('task_name')}")
    if result.get("verification", {}).get("ok"):
        lines.append("Verificacao: OK, a contagem pedida ficou confirmada.")
    else:
        lines.append("Verificacao: FALHOU, ainda ha posts em falta e isto ficou registado para correcao.")
    return "\n".join(lines)


def recent_chat_context(limit: int = 12) -> str:
    path = chat_log_path()
    if not path.exists():
        return ""
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        role = item.get("role", "unknown")
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        rows.append(f"{role}: {content[:1200]}")
    return "\n\n".join(rows)


def _extract_eve_tool_call(text: str) -> dict | None:
    calls = _extract_eve_tool_calls(text)
    return calls[0] if calls else None


def _extract_eve_tool_calls(text: str) -> list[dict]:
    marker = "EVE_TOOL"
    calls = []
    search_from = 0
    while True:
        index = text.find(marker, search_from)
        if index < 0:
            break
        payload_text = text[index + len(marker) :].lstrip()
        try:
            payload, consumed = json.JSONDecoder().raw_decode(payload_text)
        except json.JSONDecodeError:
            search_from = index + len(marker)
            continue
        if isinstance(payload, dict) and isinstance(payload.get("tool"), str):
            args = payload.get("args") or {}
            if isinstance(args, dict):
                calls.append({"tool": payload["tool"], "args": args})
        search_from = index + len(marker) + consumed
    return calls


def execute_eve_tool_call(call: dict) -> dict:
    return execute_eve_tool(call)


def format_eve_tool_result(result: dict) -> str:
    if result.get("text"):
        return str(result["text"])
    if not result.get("ok"):
        return f"Erro real na ferramenta {result.get('tool')}: {result.get('error')}"
    payload = result.get("result")
    tool = result.get("tool")
    runtime_verification = result.get("verification")
    verified = not (isinstance(runtime_verification, dict) and not runtime_verification.get("ok", True))
    if tool == "create_desktop_file":
        return f"Ficheiro criado: {payload['path']}"
    if tool == "create_desktop_folder":
        return f"Pasta criada: {payload['path']}"
    if tool == "open_browser":
        return f"Browser aberto em {payload['url']} com perfil {payload['profile_name']} ({payload['profile_directory']})."
    if tool == "schedule_desktop_folder":
        return f"Pasta agendada: {payload['folder']}\nHora: {payload['scheduled_for']}\nTarefa: {payload['task_name']}"
    if tool == "schedule_x_post":
        return format_x_schedule_result(payload)
    if tool == "publish_x_post_now":
        correction = payload.get("correction") if isinstance(payload, dict) else None
        correction_line = ""
        if isinstance(correction, dict) and correction.get("status") == "auto_shortened":
            correction_line = (
                f"\nTexto encurtado automaticamente: "
                f"{correction.get('original_characters')} -> {correction.get('characters')} caracteres."
            )
        if not verified:
            reason = runtime_verification.get("reason") if isinstance(runtime_verification, dict) else "verificacao falhou"
            return (
                "Publicacao no X NAO confirmada. "
                "A Eve nao deve tratar isto como feito.\n"
                f"Motivo: {reason}{correction_line}\n"
                f"Resultado:\n{json.dumps(payload, indent=2, ensure_ascii=False)[:5000]}"
            )
        return (
            "Publicacao no X executada e verificada pela skill trusted/x_publish_text_learning."
            f"{correction_line}\nResultado:\n{json.dumps(payload, indent=2, ensure_ascii=False)[:5000]}"
        )
    if tool == "run_terminal":
        return (
            f"Comando executado: {payload['command']}\n"
            f"Return code: {payload.get('returncode')}\n"
            f"STDOUT:\n{payload.get('stdout', '')}\n"
            f"STDERR:\n{payload.get('stderr', '')}"
        ).strip()
    if tool == "git_pull_updates":
        status = payload.get("status")
        if status == "updated":
            return (
                "Atualizacoes do GitHub puxadas para a Eve.\n"
                f"Repo: {payload.get('repo')}\n"
                f"Remote/branch: {payload.get('remote')}/{payload.get('branch')}\n"
                f"Antes: {payload.get('head_before')}\n"
                f"Depois: {payload.get('head_after')}\n"
                "Modo: fast-forward only com autostash; sem reset nem apagamento."
            )
        if status == "up_to_date":
            return (
                "Repo da Eve ja estava atualizado com o GitHub.\n"
                f"Repo: {payload.get('repo')}\n"
                f"Remote/branch: {payload.get('remote')}/{payload.get('branch')}\n"
                f"Ahead: {payload.get('ahead')} | Behind: {payload.get('behind')}"
            )
        if status == "dry_run":
            return "Plano de atualizacao GitHub:\n" + "\n".join(f"- {item}" for item in payload.get("planned_commands", []))
        return (
            "Atualizacao GitHub falhou e foi bloqueada para revisao.\n"
            f"Motivo: {payload.get('reason')}\n"
            f"Repo: {payload.get('repo')}\n"
            f"Resultado:\n{json.dumps(payload, indent=2, ensure_ascii=False)[:5000]}"
        )
    return json.dumps(payload, indent=2, ensure_ascii=False)[:6000]


def _intent_text(prompt: str) -> str:
    normalized = unicodedata.normalize("NFKD", prompt or "")
    return "".join(ch for ch in normalized.lower() if not unicodedata.combining(ch))


def _is_self_edit_request(prompt: str) -> bool:
    text = _intent_text(prompt)
    action_terms = (
        "adiciona",
        "acrescenta",
        "poe",
        "mete",
        "muda",
        "altera",
        "modifica",
        "edita",
        "corrige",
        "melhora",
        "ajusta",
        "actualiza",
        "atualiza",
        "remove",
        "apaga",
    )
    target_terms = (
        "mensagem de arranque",
        "mensagem de quando ligas",
        "quando ligas",
        "mensagem no telegram",
        "telegram",
        "bridge",
        "ficheiro",
        "ficheiros",
        "codigo",
        "runtime",
        "webui",
        "web ui",
        "retrieval",
        "awareness",
        "memoria",
        "stage 2",
        "stage2",
        "emoji",
    )
    if "self_edit" in text or "self-edit" in text:
        return True
    return any(term in text for term in action_terms) and any(term in text for term in target_terms)


def _is_self_awareness_request(prompt: str) -> bool:
    text = _intent_text(prompt)
    awareness_terms = (
        "awareness",
        "nocao",
        "consciencia",
        "estado",
        "capacidades",
        "limitacoes",
        "limites",
        "permissoes",
        "autorizacao",
        "ferramentas",
        "stage 2",
        "stage2",
        "ficheiros awareness",
    )
    self_terms = ("tens", "teus", "tuas", "ti mesma", "eve", "consegues", "podes")
    if "self-awareness" in text or "self awareness" in text:
        return True
    if any(term in text for term in awareness_terms) and any(term in text for term in self_terms):
        return True
    if "consegues mexer" in text and ("ficheiro" in text or "codigo" in text or "em ti" in text):
        return True
    return False


def _is_interest_register_request(prompt: str) -> bool:
    if _is_self_edit_request(prompt) or _is_self_awareness_request(prompt):
        return False
    text = _intent_text(prompt)
    read_terms = ("traz", "mostra", "mostrar", "ver", "ve", "ler", "le", "consulta", "abre")
    register_terms = ("registado", "registos", "registro", "registo", "logs", "ficheiros")
    daily_terms = ("diario", "diarios", "daily", "dia")
    interest_scope_terms = (
        "interesses",
        "gostos",
        "evolucao",
        "mundo",
        "world",
        "tecnologia",
        "technology",
        "personalidade",
        "personality",
        "depois da pesquisa",
        "ultima pesquisa",
    )
    has_read = any(term in text for term in read_terms)
    has_register = any(term in text for term in register_terms)
    has_daily_scope = any(term in text for term in daily_terms) or "depois da pesquisa" in text or "ultima pesquisa" in text
    has_interest_scope = any(term in text for term in interest_scope_terms)
    return has_read and has_register and has_daily_scope and has_interest_scope


def _format_self_edit_result(result: dict) -> str:
    classification = result.get("classification") or {}
    status = result.get("status", "unknown")
    risk = classification.get("risk", "unknown")
    target_area = classification.get("target_area", "unknown")
    target_files = result.get("target_files") or classification.get("target_files") or []
    lines = [
        "Pedido Stage 2 classificado.",
        f"- Estado: {status}",
        f"- Area: {target_area}",
        f"- Risco: {risk}",
    ]
    if target_files:
        lines.append(f"- Ficheiros alvo: {', '.join(str(item) for item in target_files[:6])}")
    if result.get("change_plan_path"):
        lines.append(f"- Plano: {result['change_plan_path']}")
    request_id = result.get("permission_request_id") or result.get("request_id")
    if status in {"permission_required", "special_authorization_required"}:
        lines.insert(0, "Sandro, isto esta fora das minhas permissoes actuais. Criei um pedido de autorizacao para continuares se quiseres.")
        if request_id:
            lines.append(f"- Pedido de autorizacao: {request_id}")
            lines.append("- Para listar pedidos: python scripts\\stage2_list_permission_requests.py")
            lines.append(f"- Para autorizar: python scripts\\stage2_grant_permission.py --request-id {request_id} --granted-by Sandro")
        lines.append("- Nada foi aplicado ao runtime real.")
    else:
        lines.append(f"- Resultado: {result.get('summary', 'sem resumo')}")
    tests = result.get("tests") or {}
    if tests:
        lines.append(f"- Testes: {'passaram' if tests.get('passed') else 'falharam'}")
    return "\n".join(lines)


def _answer_self_awareness_request(prompt: str, *, role: str, display_name: str, publish_to_interface: bool) -> str:
    append_chat(role, prompt, tags=["tool_request", "self_awareness"])
    _record_session_message(role, prompt, {"speaker": "sandro", "display_name": display_name, "direct_local_tool": "self_awareness"})
    _sync_vector_message(role, prompt)
    if publish_to_interface:
        publish_interface_message(display_name, prompt, target="Eve", tags=["incoming", role])
    try:
        text = answer_self_awareness_question(prompt)
        safe_print(text)
        append_chat("assistant", text, tags=["tool", "self_awareness", "direct"])
        _record_session_message("assistant", text, {"reply_to": display_name, "direct_local_tool": "self_awareness"})
        _sync_vector_message("assistant", text)
        if publish_to_interface:
            publish_interface_message("Eve", text, target=display_name, tags=["reply", "self_awareness"])
        return text
    except Exception as exc:
        text = f"Erro ao consultar self-awareness: {type(exc).__name__}: {exc}"
        safe_print(text)
        append_chat("error", text, tags=["tool_error", "self_awareness"])
        _record_session_message("error", text, {"reply_to": display_name, "direct_local_tool": "self_awareness"})
        if publish_to_interface:
            publish_interface_message("Eve", text, target=display_name, tags=["reply", "error"])
        return text


def _answer_self_edit_request(prompt: str, *, role: str, display_name: str, publish_to_interface: bool) -> str:
    append_chat(role, prompt, tags=["tool_request", "stage2_self_edit"])
    _record_session_message(role, prompt, {"speaker": "sandro", "display_name": display_name, "direct_local_tool": "stage2_self_edit"})
    _sync_vector_message(role, prompt)
    if publish_to_interface:
        publish_interface_message(display_name, prompt, target="Eve", tags=["incoming", role])
    try:
        result = execute_self_edit_request(prompt)
        text = _format_self_edit_result(result)
        safe_print(text)
        append_chat("assistant", text, tags=["tool", "stage2_self_edit", "direct", str(result.get("status", "unknown"))])
        _record_session_message("assistant", text, {"reply_to": display_name, "direct_local_tool": "stage2_self_edit", "status": result.get("status")})
        _sync_vector_message("assistant", text)
        if publish_to_interface:
            publish_interface_message("Eve", text, target=display_name, tags=["reply", "stage2_self_edit"])
        return text
    except Exception as exc:
        text = f"Erro ao criar pedido Stage 2: {type(exc).__name__}: {exc}"
        safe_print(text)
        append_chat("error", text, tags=["tool_error", "stage2_self_edit"])
        _record_session_message("error", text, {"reply_to": display_name, "direct_local_tool": "stage2_self_edit"})
        if publish_to_interface:
            publish_interface_message("Eve", text, target=display_name, tags=["reply", "error"])
        return text


def _answer_interest_register_request(prompt: str, *, role: str, display_name: str, publish_to_interface: bool) -> str:
    append_chat(role, prompt, tags=["tool_request", "interest_registers_read"])
    _record_session_message(role, prompt, {"speaker": "sandro", "display_name": display_name, "direct_local_tool": "interest_registers_read"})
    _sync_vector_message(role, prompt)
    if publish_to_interface:
        publish_interface_message(display_name, prompt, target="Eve", tags=["incoming", role])
    try:
        registers = read_daily_interest_registers()
        text = format_daily_interest_registers(registers)
        safe_print(text)
        append_chat("assistant", text, tags=["tool", "interest_registers_read", "direct"])
        _record_session_message("assistant", text, {"reply_to": display_name, "direct_local_tool": "interest_registers_read"})
        _sync_vector_message("assistant", text)
        if publish_to_interface:
            publish_interface_message("Eve", text, target=display_name, tags=["reply", "interest_registers_read"])
        return text
    except Exception as exc:
        text = f"Erro real ao ler registos diarios de interesses: {type(exc).__name__}: {exc}"
        safe_print(text)
        append_chat("error", text, tags=["tool_error", "interest_registers_read"])
        _record_session_message("error", text, {"reply_to": display_name, "direct_local_tool": "interest_registers_read"})
        if publish_to_interface:
            publish_interface_message("Eve", text, target=display_name, tags=["reply", "error"])
        return text


def handle_natural_tool_request(prompt: str, *, speaker: str = "sandro") -> bool:
    if is_capability_question(prompt):
        role = speaker_role(speaker)
        append_chat(role, prompt, tags=["tool_request", "capability_self_test", role] if role != "user" else ["tool_request", "capability_self_test"])
        text = format_capability_self_test()
        print(text)
        append_chat("assistant", text, tags=["tool", "capability_self_test"])
        return True
    role = speaker_role(speaker)
    if role != "user":
        return False
    if _is_interest_register_request(prompt):
        append_chat(role, prompt, tags=["tool_request", "interest_registers_read"])
        try:
            registers = read_daily_interest_registers()
            text = format_daily_interest_registers(registers)
            print(text)
            append_chat("assistant", text, tags=["tool", "interest_registers_read"])
        except Exception as exc:
            text = f"Erro real ao ler registos diarios de interesses: {type(exc).__name__}: {exc}"
            print(text)
            append_chat("error", text, tags=["tool_error", "interest_registers_read"])
        return True
    repeated_x = parse_natural_repeated_x_request(prompt)
    if repeated_x:
        append_chat(role, prompt, tags=["tool_request", "x_repeated_schedule"])
        try:
            result = schedule_repeated_x_posts(
                count=repeated_x["count"],
                interval_minutes=repeated_x["interval_minutes"],
                topic=repeated_x["topic"],
                approved_by="sandro",
            )
            text = format_repeated_x_schedule_result(result)
            print(text)
            append_chat("assistant", text, tags=["tool", "x_repeated_schedule", result["status"]])
        except Exception as exc:
            text = f"Erro real ao agendar posts repetidos no X: {type(exc).__name__}: {exc}"
            print(text)
            append_chat("error", text, tags=["tool_error", "x_repeated_schedule"])
        return True
    x_schedule = parse_natural_x_schedule_request(prompt)
    if x_schedule:
        append_chat(role, prompt, tags=["tool_request", "x_schedule", role] if role != "user" else ["tool_request", "x_schedule"])
        if x_schedule.get("status") == "needs_confirmation":
            text = "Preciso da hora em formato HH:MM para agendar o post no X."
            print(text)
            append_chat("assistant", text, tags=["tool", "x_schedule", "needs_confirmation"])
            return True
        try:
            result = schedule_x_post(x_schedule["text"], x_schedule["time"], approved_by="sandro")
            text = format_x_schedule_result(result)
            print(text)
            append_chat("assistant", text, tags=["tool", "x_schedule", result["status"]])
        except Exception as exc:
            text = f"Erro real ao agendar post no X: {type(exc).__name__}: {exc}"
            print(text)
            append_chat("error", text, tags=["tool_error", "x_schedule"])
        return True
    desktop_file = parse_desktop_file_request(prompt)
    desktop_folder = parse_desktop_folder_request(prompt)
    desktop_folder_schedule = parse_desktop_folder_schedule_request(prompt)
    browser_target = natural_browser_target(prompt)
    if desktop_file or desktop_folder or desktop_folder_schedule or browser_target:
        role = speaker_role(speaker)
        append_chat(role, prompt, tags=["tool_request", "compound", role] if role != "user" else ["tool_request", "compound"])
        messages = []
        if desktop_file and desktop_file.get("status") == "needs_confirmation":
            messages.append("Preciso do nome do ficheiro para criar no Ambiente de Trabalho.")
        elif desktop_file:
            try:
                result = create_desktop_file(desktop_file["name"])
                messages.append(f"Ficheiro criado: {result['path']}")
            except Exception as exc:
                messages.append(f"Erro real ao criar ficheiro no Ambiente de Trabalho: {type(exc).__name__}: {exc}")
        if desktop_folder and desktop_folder.get("status") == "needs_confirmation":
            messages.append("Preciso do nome da pasta para criar no Ambiente de Trabalho.")
        elif desktop_folder:
            try:
                result = create_desktop_folder(desktop_folder["name"])
                messages.append(f"Pasta criada: {result['path']}")
            except Exception as exc:
                messages.append(f"Erro real ao criar pasta no Ambiente de Trabalho: {type(exc).__name__}: {exc}")
        if browser_target:
            try:
                result = open_url(browser_target)
                messages.append(
                    f"Abri o navegador da Eve em {result['url']} "
                    f"com o perfil {result['profile_name']} ({result['profile_directory']})."
                )
            except Exception as exc:
                messages.append(f"Erro real ao abrir o navegador: {type(exc).__name__}: {exc}")
        if desktop_folder_schedule and desktop_folder_schedule.get("status") == "needs_confirmation":
            messages.append("Preciso da hora em formato HH:MM para agendar a criação da pasta.")
        elif desktop_folder_schedule:
            try:
                result = schedule_desktop_folder_creation(desktop_folder_schedule["name"], desktop_folder_schedule["time"])
                messages.append(
                    f"Pasta agendada: {result['folder']}\n"
                    f"Hora: {result['scheduled_for']}\n"
                    f"Tarefa: {result['task_name']}"
                )
                if result.get("note"):
                    messages.append(f"Nota: {result['note']}")
            except Exception as exc:
                messages.append(f"Erro real ao agendar pasta no Ambiente de Trabalho: {type(exc).__name__}: {exc}")
        text = "\n".join(messages)
        print(text)
        append_chat("assistant", text, tags=["tool", "compound"])
        return True
    if browser_target:
        role = speaker_role(speaker)
        append_chat(role, prompt, tags=["tool_request", role] if role != "user" else ["tool_request"])
        try:
            result = open_url(browser_target)
            text = (
                f"Abri o navegador da Eve em {result['url']} "
                f"com o perfil {result['profile_name']} ({result['profile_directory']})."
            )
            print(text)
            append_chat("assistant", text, tags=["tool", "browser"])
        except Exception as exc:
            text = f"Erro ao abrir o navegador: {exc}"
            print(text)
            append_chat("error", text, tags=["tool_error", "browser"])
        return True
    return False


def chat() -> None:
    print("Eve chat. Escreve /sair para sair.")
    print("Comandos: /menu, /voltar, /speaker sandro|codex, /codex mensagem, /memory_debug on|off, /loop objectivo, /loop-status, /loop-modo 1|2|3, /auth, /auth-contas, /auth-trocar, /auth-login nome, /dashboard, /modelo, /estado, /capacidades, /seguranca, /modo-seguranca, /liberdade-total, /seguranca-safe, /entidades-path, /entidades-files, /aprender-sandro, /entidades, /entidade, /relacao, /entidades-search, /monitores, /ocr-status, /ecra, /ecra-monitor, /ver-texto, /centro-texto, /clicar-texto, /visual-click, /vector-index, /vector-search, /vector-search2, /win-agendar, /win-tarefas, /x-agendar, /daemon-tick, /daemon-stop, /autonomia-ciclo, /autonomia-llm, /autonomia-executar, /autonomia-relatorio, /missao-executar-auto, /watch-tech, /notify, /speak, /mobile, /mobile-msg, /app-profile, /app-profiles, /demo-record, /demo-summary, /pipeline, /admin-elevado, /app, /browser, /pesquisar, /research-report, /missao-criar, /missoes, /missao, /missao-retomar, /missao-status, /missao-passo, /missao-log, /missao-checkpoint, /email-draft, /mouse, /mover, /clicar, /tecla, /hotkey, /escrever, /agenda, /agendar, /proativo, /workspace-scan, /preferencia, /preferencias, /falha-skill, /licao, /skill-note, /experiencia, /experiencia-result, /melhoria, /melhorias-erros, /patch-proposta, /sandbox, /admin, /aprovar-admin, /rsi, /lock, /unlock, /diario, /consolidar, /sonhar, /lembrar, /world, /tech, /lab, /workspace, /ls, /ler, /nota, /cmd, /aprovar-cmd, /erros, /skills, /skill-run, /skill-promote, /skill-demo")
    print("Mensagens externas de Codex-instrutor aparecem automaticamente aqui.")
    print()
    start_interface_inbox_watcher()
    current_speaker = "sandro"
    memory_debug = os.environ.get("EVE_MEMORY_DEBUG", "").lower() in {"1", "true", "yes", "on"}
    while True:
        try:
            prompt = input(f"{speaker_prompt(current_speaker)}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not prompt:
            continue
        if prompt in MENU_COMMANDS:
            prompt = MENU_COMMANDS[prompt]
        one_off_speaker = current_speaker
        if prompt.lower().startswith("/codex "):
            one_off_speaker = "codex"
            prompt = prompt.split(None, 1)[1].strip()
            if not prompt:
                continue
        if prompt.lower() in {"/sair", "/exit", "exit", "quit"}:
            return
        if prompt.lower() in {"/voltar", "/menu"}:
            print(render_menu())
            continue
        if prompt.lower() == "/chat":
            print("Modo chat ativo.")
            continue
        if prompt.lower() == "/quem-fala":
            print(f"Falante atual: {current_speaker} ({speaker_role(current_speaker)})")
            continue
        if prompt.lower() in {"/memory_debug on", "/memory-debug on"}:
            memory_debug = True
            print("Memory debug ativo.")
            continue
        if prompt.lower() in {"/memory_debug off", "/memory-debug off"}:
            memory_debug = False
            print("Memory debug inativo.")
            continue
        if prompt.lower().startswith("/speaker "):
            current_speaker = normalize_speaker(prompt.split(None, 1)[1])
            print(f"Falante atual: {current_speaker} ({speaker_role(current_speaker)})")
            continue
        if prompt.lower() == "/loop-status":
            print_loop_status()
            continue
        if prompt.lower().startswith("/loop-modo "):
            try:
                set_loop_mode(prompt.split(None, 1)[1])
            except Exception as exc:
                print(f"Erro a mudar modo do loop: {exc}")
            continue
        if prompt.lower().startswith("/loop "):
            try:
                safe_print(json.dumps(run_codex_eve_loop(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False))
            except Exception as exc:
                print(f"Erro no loop Codex-Eve: {exc}")
            continue
        if one_off_speaker == "codex" and prompt.startswith("/"):
            append_chat("codex_instructor", prompt, tags=["codex_instructor", "command"])
            publish_interface_message("codex_instructor", prompt, tags=["instructor", "command"])
        if prompt.lower() == "/dashboard":
            print(render_dashboard())
            continue
        if prompt.lower() == "/entidades-path":
            print(ENTITIES_MEMORY_DIR)
            continue
        if prompt.lower() == "/entidades-files":
            files = list_base_memory_files()
            print(json.dumps({"root": str(ENTITIES_MEMORY_DIR), "count": len(files), "files": files[:80]}, indent=2, ensure_ascii=False)[:8000])
            continue
        if prompt.lower() == "/aprender-sandro":
            try:
                result = build_sandro_core_memory(SANDRO_MEMORY_FILES)
                print(json.dumps(result, indent=2, ensure_ascii=False)[:8000])
            except Exception as exc:
                print(f"Erro a aprender memoria do Sandro: {exc}")
            continue
        if prompt.lower() == "/entidades":
            print(json.dumps(list_entities(), indent=2, ensure_ascii=False)[:5000])
            continue
        if prompt.lower().startswith("/entidade "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 2)]
                if len(parts) != 3:
                    raise ValueError("Formato: /entidade nome | tipo | nota")
                print(f"Entidade guardada em: {remember_entity(parts[0], parts[1], parts[2])}")
                print(f"Indice atualizado em: {rebuild_memory_index()}")
            except Exception as exc:
                print(f"Erro a guardar entidade: {exc}")
            continue
        if prompt.lower().startswith("/relacao "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 3)]
                if len(parts) != 4:
                    raise ValueError("Formato: /relacao origem | relacao | destino | nota")
                print(f"Relacao guardada em: {relate_entities(parts[0], parts[1], parts[2], parts[3])}")
                print(f"Indice atualizado em: {rebuild_memory_index()}")
            except Exception as exc:
                print(f"Erro a guardar relacao: {exc}")
            continue
        if prompt.lower().startswith("/entidades-search "):
            print(json.dumps(search_entities(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:8000])
            continue
        if prompt.lower() == "/modelo":
            print_model()
            continue
        if prompt.lower() == "/modelos":
            print("Modelos sugeridos:")
            for model in KNOWN_MODELS:
                print(f"  {model}")
            continue
        if prompt.lower().startswith("/modelo "):
            set_model(prompt.split(None, 1)[1])
            continue
        if prompt.lower() == "/auth":
            status()
            continue
        if prompt.lower() == "/auth-contas":
            print_auth_accounts()
            continue
        if prompt.lower() == "/auth-trocar":
            try:
                interactive_auth_switch()
            except Exception as exc:
                print(f"Erro a trocar conta: {exc}")
            print("Usa /voltar para voltar ao menu.")
            continue
        if prompt.lower().startswith("/auth-login "):
            try:
                login(prompt.split(None, 1)[1])
            except Exception as exc:
                print(f"Erro no login da conta: {exc}")
            continue
        if prompt.lower().startswith("/auth-usar "):
            try:
                select_auth_account(prompt.split(None, 1)[1])
            except Exception as exc:
                print(f"Erro a selecionar conta: {exc}")
            continue
        if prompt.lower() == "/diario":
            text = read_diary()
            print(text[-4000:] if text else "Ainda nao ha diario de hoje.")
            continue
        if prompt.lower() == "/diarios":
            days = list_diary_days()
            print("Diarios: " + (", ".join(days) if days else "nenhum"))
            continue
        if prompt.lower() == "/consolidar":
            path = consolidate_today()
            print(f"Diario consolidado em: {path}")
            continue
        if prompt.lower() == "/sonhar":
            path = run_dream()
            print(f"Relatorio de sonho criado em: {path}")
            continue
        if prompt.lower() == "/sonho-ciclo":
            payload = run_dream_cycle()
            print(f"Relatorio de sonho criado em: {payload['dream_report']}")
            print(f"Fila do lab criada em: {payload['queue']}")
            print(f"Indice vetorial atualizado em: {payload['vector_index']}")
            continue
        if prompt.lower().startswith("/lembrar "):
            path = remember_fact(prompt.split(None, 1)[1])
            print(f"Memoria guardada em: {path}")
            continue
        if prompt.lower().startswith("/world "):
            path = append_world_learning(prompt.split(None, 1)[1])
            print(f"Aprendizagem do mundo guardada em: {path}")
            continue
        if prompt.lower().startswith("/tech "):
            text = prompt.split(None, 1)[1]
            path = append_technology_learning(text)
            candidate = append_research_candidate(text)
            print(f"Aprendizagem tecnologica guardada em: {path}")
            print(f"Candidato de research guardado em: {candidate}")
            continue
        if prompt.lower().startswith("/lab "):
            payload = prompt.split(None, 1)[1]
            if "|" in payload:
                title, hypothesis = [part.strip() for part in payload.split("|", 1)]
            else:
                title, hypothesis = payload, payload
            path = create_candidate(title, hypothesis)
            print(f"Candidato de lab criado em: {path}")
            continue
        if prompt.lower() == "/lab":
            candidates = list_candidates()
            print("Lab candidates: " + (", ".join(candidates) if candidates else "nenhum"))
            continue
        if prompt.lower() == "/workspace":
            print(EVE_ROOT / "workspace")
            continue
        if prompt.lower() == "/ls":
            for item in list_dir("."):
                print(item)
            continue
        if prompt.lower().startswith("/ls "):
            for item in list_dir(prompt.split(None, 1)[1]):
                print(item)
            continue
        if prompt.lower().startswith("/ler "):
            try:
                print(read_file(prompt.split(None, 1)[1])[-6000:])
            except Exception as exc:
                print(f"Erro a ler ficheiro: {exc}")
            continue
        if prompt.lower().startswith("/nota "):
            text = prompt.split(None, 1)[1]
            path = append_file("notes.md", f"- {now_iso()}: {text}")
            print(f"Nota guardada em: {path}")
            continue
        if prompt.lower().startswith("/cmd "):
            result = run_command(prompt.split(None, 1)[1])
            if not result.get("allowed"):
                print(result["reason"])
            else:
                if result.get("stdout"):
                    print(result["stdout"])
                if result.get("stderr"):
                    print(result["stderr"])
                print(f"exit_code={result.get('returncode')}")
            continue
        if prompt.lower().startswith("/aprovar-cmd "):
            command = prompt.split(None, 1)[1]
            print("ATENCAO: comando aprovado manualmente nesta execucao.")
            result = run_command(command, approved=True)
            if result.get("stdout"):
                print(result["stdout"])
            if result.get("stderr"):
                print(result["stderr"])
            print(f"exit_code={result.get('returncode')}")
            continue
        if prompt.lower() == "/erros":
            errors = recent_errors()
            if not errors:
                print("Sem erros registados.")
            for err in errors:
                print(f"- {err.get('timestamp')} [{err.get('source')}] {err.get('error_type')}: {err.get('error_text')[:300]}")
            continue
        if prompt.lower() == "/skills":
            skills = list_skills()
            print("Skills: " + (", ".join(skills) if skills else "nenhuma"))
            continue
        if prompt.lower() in ("/estado", "/awareness"):
            print(describe_awareness())
            continue
        if prompt.lower() in ("/capacidades", "/capabilities"):
            print(format_capability_self_test())
            continue
        if prompt.lower() in ("/self-report", "/introspecao"):
            print(format_self_report("manual_self_report"))
            continue
        if prompt.lower() == "/seguranca":
            print(describe_safety())
            continue
        if prompt.lower() == "/modos-seguranca":
            for mode, profile in SAFETY_MODES.items():
                print(f"- {mode}: {profile['description']}")
            continue
        if prompt.lower().startswith("/modo-seguranca "):
            try:
                payload = prompt.split(None, 1)[1]
                if "|" in payload:
                    mode, reason = [part.strip() for part in payload.split("|", 1)]
                else:
                    mode, reason = payload.strip(), "manual"
                print(f"Modo atualizado em: {set_safety_mode(mode, reason)}")
                print(describe_safety())
            except Exception as exc:
                print(f"Erro a mudar seguranca: {exc}")
            continue
        if prompt.lower().startswith("/liberdade-total"):
            reason = prompt.split(None, 1)[1] if " " in prompt else "Sandro ativou liberdade total manualmente"
            print(f"Modo atualizado em: {set_safety_mode('unrestricted_mode', reason)}")
            print(describe_safety())
            continue
        if prompt.lower().startswith("/seguranca-safe"):
            reason = prompt.split(None, 1)[1] if " " in prompt else "Sandro voltou a ligar seguranca"
            print(f"Modo atualizado em: {set_safety_mode('safe_mode', reason)}")
            print(describe_safety())
            continue
        if prompt.lower() == "/monitores":
            print(json.dumps(monitor_report(), indent=2, ensure_ascii=False)[:6000])
            continue
        if prompt.lower() == "/ocr-status":
            print(json.dumps(ocr_status(), indent=2, ensure_ascii=False))
            continue
        if prompt.lower() == "/ecra":
            try:
                print(json.dumps(describe_screen(), indent=2, ensure_ascii=False)[:6000])
            except Exception as exc:
                print(f"Erro a observar ecra: {exc}")
            continue
        if prompt.lower().startswith("/ecra-monitor "):
            try:
                print(json.dumps(screenshot_monitor(int(prompt.split(None, 1)[1])), indent=2, ensure_ascii=False)[:4000])
            except Exception as exc:
                print(f"Erro a capturar monitor: {exc}")
            continue
        if prompt.lower().startswith("/ver-texto "):
            try:
                print(json.dumps(find_text_on_screen(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:6000])
            except Exception as exc:
                print(f"Erro a procurar texto no ecra: {exc}")
            continue
        if prompt.lower().startswith("/centro-texto "):
            try:
                print(json.dumps(first_text_center(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:5000])
            except Exception as exc:
                print(f"Erro a calcular centro do texto: {exc}")
            continue
        if prompt.lower().startswith("/clicar-texto "):
            try:
                target = first_text_center(prompt.split(None, 1)[1])
                if not target.get("found"):
                    print(json.dumps(target, indent=2, ensure_ascii=False)[:5000])
                else:
                    print(json.dumps(click(int(target["x"]), int(target["y"])), indent=2, ensure_ascii=False)[:4000])
            except Exception as exc:
                print(f"Erro a clicar texto: {exc}")
            continue
        if prompt.lower().startswith("/visual-click "):
            try:
                payload = prompt.split(None, 1)[1]
                if "|" in payload:
                    target_text, verify_text = [part.strip() for part in payload.split("|", 1)]
                else:
                    target_text, verify_text = payload.strip(), None
                print(json.dumps(click_text_and_verify(target_text, verify_text), indent=2, ensure_ascii=False)[:7000])
            except Exception as exc:
                print(f"Erro visual executor: {exc}")
            continue
        if prompt.lower() == "/vector-index":
            print(f"Indice vetorial reconstruido em: {rebuild_memory_index()}")
            continue
        if prompt.lower().startswith("/vector-search "):
            print(json.dumps(vector_search(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:6000])
            continue
        if prompt.lower().startswith("/vector-search2 "):
            print(json.dumps(search_tfidf(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:6000])
            continue
        if prompt.lower().startswith("/win-agendar "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 1)]
                if len(parts) != 2:
                    raise ValueError("Formato: /win-agendar nome | HH:MM")
                print(json.dumps(create_daily_task(parts[0], parts[1]), indent=2, ensure_ascii=False)[:5000])
            except Exception as exc:
                print(f"Erro a criar tarefa Windows: {exc}")
            continue
        if prompt.lower().startswith("/x-agendar "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 1)]
                if len(parts) != 2:
                    raise ValueError("Formato: /x-agendar HH:MM | texto")
                result = schedule_x_post(parts[1], parts[0], approved_by="sandro")
                print(format_x_schedule_result(result))
            except Exception as exc:
                print(f"Erro a agendar post no X: {exc}")
            continue
        if prompt.lower() == "/win-tarefas":
            print(json.dumps(list_eve_tasks(), indent=2, ensure_ascii=False)[:5000])
            continue
        if prompt.lower() == "/daemon-tick":
            print(json.dumps(daemon_tick(), indent=2, ensure_ascii=False)[:5000])
            continue
        if prompt.lower() == "/daemon-stop":
            print(f"Daemon stop pedido em: {request_daemon_stop()}")
            continue
        if prompt.lower() == "/autonomia-ciclo":
            print(json.dumps(run_autonomy_cycle(triggers=["manual"], call_llm="auto"), indent=2, ensure_ascii=False)[:9000])
            continue
        if prompt.lower() == "/autonomia-llm":
            print(json.dumps(run_autonomy_cycle(triggers=["manual", "llm_review"], call_llm=True), indent=2, ensure_ascii=False)[:9000])
            continue
        if prompt.lower() == "/autonomia-executar":
            print(json.dumps(execute_autonomous_backlog(max_missions=2, notify_chat=True), indent=2, ensure_ascii=False)[:7000])
            continue
        if prompt.lower() == "/autonomia-relatorio":
            print(json.dumps(run_autonomy_report_cycle(call_llm="auto"), indent=2, ensure_ascii=False)[:9000])
            continue
        if prompt.lower().startswith("/missao-executar-auto "):
            try:
                print(json.dumps(execute_autonomous_mission(prompt.split(None, 1)[1].strip(), notify_chat=True), indent=2, ensure_ascii=False)[:7000])
            except Exception as exc:
                print(f"Erro a executar missao autonoma: {exc}")
            continue
        if prompt.lower() == "/watch-tech":
            print(f"Technology watch guardado em: {run_technology_watch()}")
            continue
        if prompt.lower().startswith("/notify "):
            payload = prompt.split(None, 1)[1]
            if "|" in payload:
                title, message = [part.strip() for part in payload.split("|", 1)]
            else:
                title, message = "Eve", payload
            print(json.dumps(notify(title, message), indent=2, ensure_ascii=False)[:3000])
            continue
        if prompt.lower().startswith("/speak "):
            print(json.dumps(speak(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:3000])
            continue
        if prompt.lower() == "/mobile":
            print(json.dumps(bridge_status(), indent=2, ensure_ascii=False))
            continue
        if prompt.lower().startswith("/mobile-msg "):
            print(f"Mensagem mobile em fila: {queue_mobile_message(prompt.split(None, 1)[1])}")
            continue
        if prompt.lower().startswith("/app-profile"):
            name = prompt.split(None, 1)[1] if " " in prompt else None
            print(f"Perfil de app guardado em: {capture_app_profile(name)}")
            continue
        if prompt.lower() == "/app-profiles":
            print(", ".join(list_app_profiles()) or "sem perfis")
            continue
        if prompt.lower().startswith("/demo-record "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 2)]
                name = parts[0]
                seconds = int(parts[1]) if len(parts) > 1 else 30
                description = parts[2] if len(parts) > 2 else ""
                print(f"Gravacao guardada em: {record_user_demonstration(name, seconds, description)}")
            except Exception as exc:
                print(f"Erro a gravar demonstracao: {exc}")
            continue
        if prompt.lower().startswith("/demo-summary "):
            print(json.dumps(summarize_demonstration(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:4000])
            continue
        if prompt.lower().startswith("/pipeline "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 3)]
                if len(parts) < 3:
                    raise ValueError("Formato: /pipeline area | problema | proposta | patch_opcional")
                print(json.dumps(run_improvement_pipeline(parts[0], parts[1], parts[2], parts[3] if len(parts) > 3 else ""), indent=2, ensure_ascii=False)[:6000])
            except Exception as exc:
                print(f"Erro no pipeline: {exc}")
            continue
        if prompt.lower().startswith("/admin-elevado "):
            print(json.dumps(launch_elevated_powershell(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:4000])
            continue
        if prompt.lower().startswith("/browser "):
            try:
                print(json.dumps(open_url(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:4000])
            except Exception as exc:
                print(f"Erro no browser: {exc}")
            continue
        if prompt.lower().startswith("/pesquisar "):
            try:
                print(json.dumps(search_web(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:4000])
            except Exception as exc:
                print(f"Erro na pesquisa: {exc}")
            continue
        if prompt.lower().startswith("/research-report "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|")]
                query = parts[0]
                args = {"query": query}
                if len(parts) > 1 and parts[1]:
                    args["seed_urls"] = parts[1]
                if len(parts) > 2 and parts[2]:
                    args["allowed_domains"] = parts[2]
                if len(parts) > 3 and parts[3]:
                    args["max_pages"] = parts[3]
                result = run_skill("trusted/web_research_report", args=args)
                print(json.dumps(result, indent=2, ensure_ascii=False)[:6000])
            except Exception as exc:
                print(f"Erro no research report: {exc}")
            continue
        if prompt.lower().startswith("/missao-criar "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|")]
                objective = parts[0]
                plan = [item.strip() for item in parts[1].split(";") if item.strip()] if len(parts) > 1 and parts[1] else []
                permissions = [item.strip() for item in parts[2].split(",") if item.strip()] if len(parts) > 2 and parts[2] else []
                mission = create_mission(objective, plan=plan, permissions=permissions)
                print(json.dumps(mission, indent=2, ensure_ascii=False)[:6000])
            except Exception as exc:
                print(f"Erro a criar missao: {exc}")
            continue
        if prompt.lower() == "/missoes":
            print(json.dumps(list_missions(), indent=2, ensure_ascii=False)[:6000])
            continue
        if prompt.lower().startswith("/missao-retomar "):
            try:
                print(json.dumps(resume_summary(prompt.split(None, 1)[1].strip()), indent=2, ensure_ascii=False)[:4000])
            except Exception as exc:
                print(f"Erro a retomar missao: {exc}")
            continue
        if prompt.lower().startswith("/missao-status "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 2)]
                print(json.dumps(set_mission_status(parts[0], parts[1], reason=parts[2] if len(parts) > 2 else "", actor="eve"), indent=2, ensure_ascii=False)[:5000])
            except Exception as exc:
                print(f"Erro a mudar estado da missao: {exc}")
            continue
        if prompt.lower().startswith("/missao-passo "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 3)]
                print(json.dumps(mission_update_step(parts[0], int(parts[1]), parts[2], note=parts[3] if len(parts) > 3 else "", actor="eve"), indent=2, ensure_ascii=False)[:5000])
            except Exception as exc:
                print(f"Erro a atualizar passo da missao: {exc}")
            continue
        if prompt.lower().startswith("/missao-log "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 1)]
                print(json.dumps(append_mission_log(parts[0], "eve", parts[1] if len(parts) > 1 else ""), indent=2, ensure_ascii=False)[:5000])
            except Exception as exc:
                print(f"Erro no log da missao: {exc}")
            continue
        if prompt.lower().startswith("/missao-checkpoint "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 2)]
                data = json.loads(parts[2]) if len(parts) > 2 and parts[2] else {}
                print(json.dumps(mission_add_checkpoint(parts[0], parts[1], data), indent=2, ensure_ascii=False)[:5000])
            except Exception as exc:
                print(f"Erro no checkpoint da missao: {exc}")
            continue
        if prompt.lower().startswith("/missao "):
            try:
                print(json.dumps(load_mission(prompt.split(None, 1)[1].strip()), indent=2, ensure_ascii=False)[:6000])
            except Exception as exc:
                print(f"Erro a ler missao: {exc}")
            continue
        if prompt.lower().startswith("/email-draft "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 2)]
                if len(parts) != 3:
                    raise ValueError("Formato: /email-draft para | assunto | corpo")
                print(json.dumps(create_gmail_draft(parts[0], parts[1], parts[2]), indent=2, ensure_ascii=False)[:5000])
            except Exception as exc:
                print(f"Erro a criar rascunho: {exc}")
            continue
        if prompt.lower() == "/agenda":
            print(json.dumps(list_scheduled_tasks(), indent=2, ensure_ascii=False)[:5000])
            continue
        if prompt.lower().startswith("/agendar "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 2)]
                if len(parts) != 3:
                    raise ValueError("Formato: /agendar nome | cadencia | acao")
                print(f"Tarefa agendada em: {add_scheduled_task(parts[0], parts[1], parts[2])}")
            except Exception as exc:
                print(f"Erro a agendar: {exc}")
            continue
        if prompt.lower() == "/proativo":
            for item in propose_low_risk_actions():
                print(f"- {item}")
            continue
        if prompt.lower() == "/workspace-scan":
            print(json.dumps(workspace_snapshot(), indent=2, ensure_ascii=False)[:5000])
            continue
        if prompt.lower() == "/app":
            try:
                print(json.dumps(observe_active_app(), indent=2, ensure_ascii=False)[:6000])
            except Exception as exc:
                print(f"Erro a observar app: {exc}")
            continue
        if prompt.lower().startswith("/preferencia "):
            payload = prompt.split(None, 1)[1]
            if "|" in payload:
                pref, reason = [part.strip() for part in payload.split("|", 1)]
            else:
                pref, reason = payload, ""
            print(f"Preferencia guardada em: {add_preference(pref, reason)}")
            continue
        if prompt.lower() == "/preferencias":
            print(read_preferences()[-5000:] or "Sem preferencias evolutivas.")
            continue
        if prompt.lower().startswith("/falha-skill "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 3)]
                if len(parts) < 3:
                    raise ValueError("Formato: /falha-skill skill | passo | erro | observacao")
                print(f"Falha registada em: {record_skill_failure(parts[0], parts[1], parts[2], parts[3] if len(parts) > 3 else '')}")
            except Exception as exc:
                print(f"Erro a registar falha: {exc}")
            continue
        if prompt.lower().startswith("/licao "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 3)]
                if len(parts) != 4:
                    raise ValueError("Formato: /licao skill | problema | correcao | licao")
                print(f"Licao registada em: {record_adaptive_lesson(parts[0], parts[1], parts[2], parts[3])}")
            except Exception as exc:
                print(f"Erro a registar licao: {exc}")
            continue
        if prompt.lower().startswith("/skill-note "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 1)]
                if len(parts) != 2:
                    raise ValueError("Formato: /skill-note skill | nota")
                print(f"Skill atualizada em: {add_skill_note(parts[0], parts[1])}")
            except Exception as exc:
                print(f"Erro a atualizar skill: {exc}")
            continue
        if prompt.lower().startswith("/experiencia "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 3)]
                if len(parts) != 4:
                    raise ValueError("Formato: /experiencia titulo | hipotese | metrica | procedimento")
                print(f"Experiencia criada em: {create_experiment(parts[0], parts[1], parts[2], parts[3])}")
            except Exception as exc:
                print(f"Erro a criar experiencia: {exc}")
            continue
        if prompt.lower().startswith("/experiencia-result "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 2)]
                if len(parts) != 3:
                    raise ValueError("Formato: /experiencia-result nome | resultado | decisao")
                print(f"Resultado guardado em: {record_experiment_result(parts[0], parts[1], parts[2])}")
            except Exception as exc:
                print(f"Erro a guardar resultado: {exc}")
            continue
        if prompt.lower().startswith("/melhoria "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 3)]
                if len(parts) < 3:
                    raise ValueError("Formato: /melhoria area | problema | proposta | risco")
                print(f"Melhoria proposta em: {propose_improvement(parts[0], parts[1], parts[2], parts[3] if len(parts) > 3 else 'low')}")
            except Exception as exc:
                print(f"Erro a propor melhoria: {exc}")
            continue
        if prompt.lower() == "/melhorias-erros":
            paths = propose_from_recent_errors()
            print("Melhorias propostas: " + (", ".join(str(path) for path in paths) if paths else "nenhuma"))
            continue
        if prompt.lower().startswith("/patch-proposta "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 2)]
                if len(parts) != 3:
                    raise ValueError("Formato: /patch-proposta nome | resumo | diff")
                print(f"Patch proposto em: {write_patch_proposal(parts[0], parts[1], parts[2])}")
            except Exception as exc:
                print(f"Erro a criar patch proposta: {exc}")
            continue
        if prompt.lower().startswith("/sandbox "):
            paths = [part.strip() for part in prompt.split(None, 1)[1].split() if part.strip()]
            print(json.dumps(run_python_compile(paths), indent=2, ensure_ascii=False)[:5000])
            continue
        if prompt.lower().startswith("/admin "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 1)]
                if len(parts) != 2:
                    raise ValueError("Formato: /admin motivo | comando")
                print(json.dumps(run_admin_command(parts[1], parts[0], approved=False), indent=2, ensure_ascii=False)[:5000])
            except Exception as exc:
                print(f"Erro admin: {exc}")
            continue
        if prompt.lower().startswith("/aprovar-admin "):
            try:
                parts = [part.strip() for part in prompt.split(None, 1)[1].split("|", 1)]
                if len(parts) != 2:
                    raise ValueError("Formato: /aprovar-admin motivo | comando")
                print(json.dumps(run_admin_command(parts[1], parts[0], approved=True), indent=2, ensure_ascii=False)[:5000])
            except Exception as exc:
                print(f"Erro admin aprovado: {exc}")
            continue
        if prompt.lower() == "/rsi":
            print(json.dumps(run_controlled_rsi_cycle(), indent=2, ensure_ascii=False)[:7000])
            continue
        if prompt.lower() == "/mouse":
            print(json.dumps(mouse_position(), indent=2, ensure_ascii=False))
            continue
        if prompt.lower().startswith("/mover "):
            try:
                _, x, y = prompt.split(None, 2)
                print(json.dumps(move_mouse(int(x), int(y)), indent=2, ensure_ascii=False)[:4000])
            except Exception as exc:
                print(f"Erro a mover rato: {exc}")
            continue
        if prompt.lower().startswith("/clicar "):
            try:
                _, x, y = prompt.split(None, 2)
                print(json.dumps(click(int(x), int(y)), indent=2, ensure_ascii=False)[:4000])
            except Exception as exc:
                print(f"Erro a clicar: {exc}")
            continue
        if prompt.lower().startswith("/tecla "):
            try:
                print(json.dumps(press_key(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:4000])
            except Exception as exc:
                print(f"Erro na tecla: {exc}")
            continue
        if prompt.lower().startswith("/hotkey "):
            try:
                keys = [part.strip() for part in prompt.split(None, 1)[1].split("+") if part.strip()]
                print(json.dumps(hotkey(*keys), indent=2, ensure_ascii=False)[:4000])
            except Exception as exc:
                print(f"Erro no hotkey: {exc}")
            continue
        if prompt.lower().startswith("/escrever "):
            try:
                print(json.dumps(type_text(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:4000])
            except Exception as exc:
                print(f"Erro a escrever: {exc}")
            continue
        if prompt.lower().startswith("/lock"):
            reason = prompt.split(None, 1)[1] if " " in prompt else "manual"
            print(f"Emergency lock ativo: {enable_emergency_lock(reason)}")
            continue
        if prompt.lower() == "/unlock":
            clear_emergency_lock()
            print("Emergency lock limpo.")
            continue
        if prompt.lower() == "/lock-status":
            print("Emergency lock: " + ("ativo" if emergency_locked() else "inativo"))
            continue
        if prompt.lower().startswith("/skill-run "):
            try:
                payload = prompt.split(None, 1)[1]
                parts = payload.split("|")
                skill = parts[0].strip()
                args = {}
                for item in parts[1:]:
                    if "=" in item:
                        key, value = item.split("=", 1)
                        args[key.strip()] = value.strip()
                result = run_skill(skill, args=args)
                print(json.dumps(result, indent=2, ensure_ascii=False)[:6000])
            except Exception as exc:
                print(f"Erro na skill: {exc}")
            continue
        if prompt.lower().startswith("/skill-promote "):
            try:
                path = promote_skill(prompt.split(None, 1)[1].strip())
                print(f"Skill promovida para trusted: {path}")
            except Exception as exc:
                print(f"Erro a promover skill: {exc}")
            continue
        if prompt.lower().startswith("/skill-demo "):
            try:
                payload = prompt.split(None, 1)[1]
                parts = [part.strip() for part in payload.split("|")]
                name = parts[0]
                description = parts[1] if len(parts) > 1 else name
                step_text = parts[2] if len(parts) > 2 else ""
                if step_text.startswith("append:"):
                    _, path, content = step_text.split(":", 2)
                    steps = [{"action": "append_file", "path": path, "content": content}]
                elif step_text.startswith("write:"):
                    _, path, content = step_text.split(":", 2)
                    steps = [{"action": "write_file", "path": path, "content": content}]
                else:
                    raise ValueError("Formato: /skill-demo nome | descricao | append:ficheiro:texto")
                path = create_skill_from_demonstration(name, description, steps)
                print(f"Skill draft criada: {path}")
            except Exception as exc:
                print(f"Erro a criar demonstracao: {exc}")
            continue
        print("eve> ", end="", flush=True)
        ask(prompt, speaker=one_off_speaker, publish_to_interface=False, enable_terminal_memory=True, memory_debug=memory_debug)
        print()


def set_model(model: str) -> None:
    config = load_config()
    config["model"] = model.strip() or DEFAULT_MODEL
    save_config(config)
    print(f"Modelo definido: {config['model']}")


def print_model() -> None:
    config = load_config()
    print(f"Modelo atual: {config.get('model') or DEFAULT_MODEL}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Eve Codex OAuth/client")
    sub = parser.add_subparsers(dest="cmd", required=True)
    login_p = sub.add_parser("login")
    login_p.add_argument("--account", default="default")
    sub.add_parser("status")
    sub.add_parser("accounts")
    use_p = sub.add_parser("use-account")
    use_p.add_argument("account")
    sub.add_parser("chat")
    sub.add_parser("current-model")
    sub.add_parser("models")
    sub.add_parser("loop-status")
    sub.add_parser("capabilities")
    loop_mode_p = sub.add_parser("loop-mode")
    loop_mode_p.add_argument("mode")
    loop_p = sub.add_parser("loop")
    loop_p.add_argument("objective")
    loop_p.add_argument("--mode", default=None)
    x_schedule_p = sub.add_parser("x-schedule")
    x_schedule_p.add_argument("time")
    x_schedule_p.add_argument("text")
    ask_p = sub.add_parser("ask")
    ask_p.add_argument("prompt")
    ask_p.add_argument("--speaker", default="sandro", choices=["sandro", "codex", "eve_initiative"])
    model_p = sub.add_parser("model")
    model_p.add_argument("model")
    args = parser.parse_args()

    if args.cmd == "login":
        login(args.account)
    elif args.cmd == "status":
        status()
    elif args.cmd == "accounts":
        print_auth_accounts()
    elif args.cmd == "use-account":
        select_auth_account(args.account)
    elif args.cmd == "chat":
        chat()
    elif args.cmd == "current-model":
        print_model()
    elif args.cmd == "models":
        print("Modelos sugeridos:")
        for model in KNOWN_MODELS:
            print(f"  {model}")
    elif args.cmd == "loop-status":
        print_loop_status()
    elif args.cmd == "capabilities":
        print(format_capability_self_test())
    elif args.cmd == "loop-mode":
        set_loop_mode(args.mode)
    elif args.cmd == "loop":
        safe_print(json.dumps(run_codex_eve_loop(args.objective, mode=args.mode), indent=2, ensure_ascii=False))
    elif args.cmd == "x-schedule":
        safe_print(json.dumps(schedule_x_post(args.text, args.time, approved_by="sandro"), indent=2, ensure_ascii=False))
    elif args.cmd == "ask":
        ask(args.prompt, speaker=args.speaker, enable_terminal_memory=True)
    elif args.cmd == "model":
        set_model(args.model)


if __name__ == "__main__":
    main()
