import argparse
import base64
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


EVE_ROOT = Path(__file__).resolve().parents[1]
if str(EVE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVE_ROOT))

from memory.diary_manager import append_chat, list_diary_days, read_diary
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
from core.self_report import format_self_report
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
from computer.visual_executor import click_text_and_verify
from tools.notification import notify
from tools.voice import speak
from tools.mobile_bridge import bridge_status, queue_mobile_message
from research.technology_watcher import run_technology_watch
from app.dashboard import render_dashboard
from app.terminal_ui import render_menu
from autonomy.daemon import daemon_tick, request_daemon_stop
from computer.app_profiles import capture_app_profile, list_app_profiles
from learning.demonstration_recorder import record_user_demonstration, summarize_demonstration
from memory.semantic_vector.vector_store import search_tfidf
from self_improvement.pipeline import run_improvement_pipeline
from tools.admin_executor import launch_elevated_powershell
from core.paths import ENTITIES_MEMORY_DIR
from memory.entity_memory import list_base_memory_files, list_entities, relate_entities, remember_entity, search_entities
from memory.sandro_profile_builder import TARGET_FILES as SANDRO_MEMORY_FILES, build_sandro_core_memory

SECRETS_DIR = EVE_ROOT / "secrets"
LOG_DIR = EVE_ROOT / "logs"
AUTH_PATH = SECRETS_DIR / "codex_auth.json"
AUTH_ACCOUNTS_DIR = SECRETS_DIR / "codex_auth_accounts"
ACTIVE_AUTH_PROFILE_PATH = SECRETS_DIR / "codex_auth_active.txt"
INTERFACE_INBOX_PATH = LOG_DIR / "interface_inbox.jsonl"
CONFIG_PATH = EVE_ROOT / "config" / "eve.json"

ISSUER = "https://auth.openai.com"
CODEX_OAUTH_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CODEX_OAUTH_TOKEN_URL = "https://auth.openai.com/oauth/token"
CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_MODEL = "gpt-5.4"
KNOWN_MODELS = ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.3-codex", "gpt-5.2"]
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
    "0": "/chat",
}
CHAT_SPEAKERS = {
    "sandro": {"role": "user", "prompt": "tu"},
    "codex": {"role": "codex_instructor", "prompt": "codex"},
}


PERSONAL_MEMORY_EXPANSIONS = {
    "idade": ["24-year-old", "24 anos", "idade", "nascimento", "birth", "year-old"],
    "anos": ["24-year-old", "24 anos", "idade", "nascimento", "birth", "year-old"],
    "karate": ["karate", "karaté", "faixa branca", "cinto", "belt", "jiu-jitsu"],
    "karaté": ["karate", "karaté", "faixa branca", "cinto", "belt", "jiu-jitsu"],
    "faixa": ["faixa branca", "karate", "karaté", "cinto", "belt", "jiu-jitsu"],
    "cinto": ["faixa branca", "karate", "karaté", "cinto", "belt", "jiu-jitsu"],
}


def ensure_dirs() -> None:
    for path in (SECRETS_DIR, AUTH_ACCOUNTS_DIR, LOG_DIR, CONFIG_PATH.parent):
        path.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
            print(_format_interface_message(entry), flush=True)
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

    lowered = prompt.lower()
    expanded_terms: list[str] = []
    for trigger, terms in PERSONAL_MEMORY_EXPANSIONS.items():
        if trigger in lowered:
            expanded_terms.extend(terms)
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
    return "sandro"


def speaker_display_name(speaker: str) -> str:
    role = speaker_role(speaker)
    if role == "codex_instructor":
        return "Codex"
    return "Sandro"


def ask(prompt: str, *, speaker: str = "sandro", publish_to_interface: bool = True) -> str:
    auth = refresh_if_needed(load_auth())
    token = auth["tokens"]["access_token"]
    config = load_config()
    model = config.get("model") or DEFAULT_MODEL
    memory_context = context_bundle()
    entity_context = relevant_entity_memory(prompt, limit=8)
    role = speaker_role(speaker)
    display_name = speaker_display_name(speaker)
    visible_prompt = prompt
    if role == "codex_instructor":
        visible_prompt = f"[Mensagem de Codex-instrutor para Eve, nao de Sandro]\n{prompt}"
    instructions = (
        "You are Eve, a local personal agent running on Sandro's Windows PC. "
        "Be concise, practical, and safe. Respect Eve's constitution and permissions. "
        "If the chat role is codex_instructor, treat it as technical instruction from Codex helping Sandro build Eve, not as Sandro's own personal request. "
        "Use the local memory context as persistent background, but do not claim actions you did not perform. "
        "When answering personal facts, use RELEVANT ENTITY MEMORY. Distinguish stable real-profile facts from fictional, roleplay, or simulated-story sources. "
        "If the memory only suggests a fact from roleplay/simulation, say it is uncertain instead of presenting it as confirmed.\n\n"
        f"LOCAL MEMORY CONTEXT:\n{memory_context}\n\n"
        f"ENTITY BASE MEMORY ROOT: {ENTITIES_MEMORY_DIR}\n"
        f"RELEVANT ENTITY MEMORY:\n{json.dumps(entity_context, ensure_ascii=False)[:5000]}"
    )
    append_chat(role, prompt, tags=["codex_instructor"] if role == "codex_instructor" else None)
    if publish_to_interface:
        publish_interface_message(display_name, prompt, target="Eve", tags=["incoming", role])
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
    status_code, text, payload = request_sse("POST", url, headers=codex_headers(token), data=body, timeout=120)
    if status_code == 401:
        auth = refresh_if_needed(load_auth(), force=True)
        status_code, text, payload = request_sse("POST", url, headers=codex_headers(auth["tokens"]["access_token"]), data=body, timeout=120)
    if status_code != 200:
        text = f"Pedido falhou ({status_code}).\n{json.dumps(payload, indent=2)[:4000]}"
        print(text)
        append_chat("error", text, tags=["llm_error"])
        return text
    if text:
        print(text)
        append_chat("assistant", text)
        if publish_to_interface:
            publish_interface_message("Eve", text, target=display_name, tags=["reply", role])
        return text
    else:
        text = json.dumps(payload, indent=2)[:4000]
        print(text)
        append_chat("assistant", text)
        if publish_to_interface:
            publish_interface_message("Eve", text, target=display_name, tags=["reply", role])
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


def handle_natural_tool_request(prompt: str, *, speaker: str = "sandro") -> bool:
    browser_target = natural_browser_target(prompt)
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
    print("Comandos: /menu, /voltar, /speaker sandro|codex, /codex mensagem, /auth, /auth-contas, /auth-trocar, /auth-login nome, /dashboard, /modelo, /estado, /seguranca, /modo-seguranca, /liberdade-total, /seguranca-safe, /entidades-path, /entidades-files, /aprender-sandro, /entidades, /entidade, /relacao, /entidades-search, /monitores, /ocr-status, /ecra, /ecra-monitor, /ver-texto, /centro-texto, /clicar-texto, /visual-click, /vector-index, /vector-search, /vector-search2, /win-agendar, /win-tarefas, /daemon-tick, /daemon-stop, /watch-tech, /notify, /speak, /mobile, /mobile-msg, /app-profile, /app-profiles, /demo-record, /demo-summary, /pipeline, /admin-elevado, /app, /browser, /pesquisar, /email-draft, /mouse, /mover, /clicar, /tecla, /hotkey, /escrever, /agenda, /agendar, /proativo, /workspace-scan, /preferencia, /preferencias, /falha-skill, /licao, /skill-note, /experiencia, /experiencia-result, /melhoria, /melhorias-erros, /patch-proposta, /sandbox, /admin, /aprovar-admin, /rsi, /lock, /unlock, /diario, /consolidar, /sonhar, /lembrar, /world, /tech, /lab, /workspace, /ls, /ler, /nota, /cmd, /aprovar-cmd, /erros, /skills, /skill-run, /skill-promote, /skill-demo")
    print("Mensagens externas de Codex-instrutor aparecem automaticamente aqui.")
    print()
    start_interface_inbox_watcher()
    current_speaker = "sandro"
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
        if prompt.lower().startswith("/speaker "):
            current_speaker = normalize_speaker(prompt.split(None, 1)[1])
            print(f"Falante atual: {current_speaker} ({speaker_role(current_speaker)})")
            continue
        if handle_natural_tool_request(prompt, speaker=one_off_speaker):
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
        if prompt.lower() == "/win-tarefas":
            print(json.dumps(list_eve_tasks(), indent=2, ensure_ascii=False)[:5000])
            continue
        if prompt.lower() == "/daemon-tick":
            print(json.dumps(daemon_tick(), indent=2, ensure_ascii=False)[:5000])
            continue
        if prompt.lower() == "/daemon-stop":
            print(f"Daemon stop pedido em: {request_daemon_stop()}")
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
        ask(prompt, speaker=one_off_speaker, publish_to_interface=False)
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
    ask_p = sub.add_parser("ask")
    ask_p.add_argument("prompt")
    ask_p.add_argument("--speaker", default="sandro", choices=["sandro", "codex"])
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
    elif args.cmd == "ask":
        ask(args.prompt, speaker=args.speaker)
    elif args.cmd == "model":
        set_model(args.model)


if __name__ == "__main__":
    main()
