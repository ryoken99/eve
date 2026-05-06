import argparse
import base64
import json
import os
import subprocess
import sys
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
from research.research_notes import append_research_candidate, append_technology_learning, append_world_learning
from lab.lab_manager import create_candidate, list_candidates
from memory.errors.error_memory import recent_errors
from core.awareness_engine import describe_awareness
from computer.vision import describe_screen, find_text_on_screen
from computer.emergency_stop import clear_emergency_lock, enable_emergency_lock, emergency_locked
from computer.mouse_control import click, mouse_position, move_mouse
from computer.keyboard_control import hotkey, press_key, type_text

SECRETS_DIR = EVE_ROOT / "secrets"
LOG_DIR = EVE_ROOT / "logs"
AUTH_PATH = SECRETS_DIR / "codex_auth.json"
CONFIG_PATH = EVE_ROOT / "config" / "eve.json"

ISSUER = "https://auth.openai.com"
CODEX_OAUTH_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CODEX_OAUTH_TOKEN_URL = "https://auth.openai.com/oauth/token"
CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_MODEL = "gpt-5.4"
KNOWN_MODELS = ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.3-codex", "gpt-5.2"]


def ensure_dirs() -> None:
    for path in (SECRETS_DIR, LOG_DIR, CONFIG_PATH.parent):
        path.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def save_auth(payload: dict) -> None:
    ensure_dirs()
    AUTH_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if os.name == "nt":
        # Best effort: keep token file readable by current user/admin/system only.
        subprocess.run(
            ["icacls", str(AUTH_PATH), "/inheritance:r", "/grant:r", f"{os.getlogin()}:R", "Administrators:F", "SYSTEM:F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def load_auth() -> dict:
    if not AUTH_PATH.exists():
        raise SystemExit("Nao ha login Codex guardado. Usa a opcao 1 primeiro.")
    return json.loads(AUTH_PATH.read_text(encoding="utf-8"))


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
    save_auth(auth)
    return auth


def login() -> None:
    ensure_dirs()
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
        "auth_mode": "chatgpt",
        "base_url": CODEX_BASE_URL,
        "created_at": now_iso(),
        "last_refresh": now_iso(),
        "tokens": {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token", ""),
        },
    }
    save_auth(auth)
    print(f"Login guardado em: {AUTH_PATH}")
    print("Chat com LLM disponivel.")


def status() -> None:
    if not AUTH_PATH.exists():
        print("Codex OAuth: nao autenticado")
        return
    auth = load_auth()
    token = (auth.get("tokens") or {}).get("access_token", "")
    claims = jwt_claims(token)
    print("Codex OAuth: autenticado")
    print(f"Ficheiro: {AUTH_PATH}")
    print(f"Criado:   {auth.get('created_at')}")
    print(f"Refresh:  {auth.get('last_refresh')}")
    print(f"Expira:   {datetime.fromtimestamp(claims.get('exp', 0), timezone.utc).isoformat() if claims.get('exp') else 'desconhecido'}")
    acct = claims.get("https://api.openai.com/auth", {}).get("chatgpt_account_id")
    if acct:
        print(f"Conta:    {acct}")


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


def ask(prompt: str) -> str:
    auth = refresh_if_needed(load_auth())
    token = auth["tokens"]["access_token"]
    config = load_config()
    model = config.get("model") or DEFAULT_MODEL
    memory_context = context_bundle()
    instructions = (
        "You are Eve, a local personal agent running on Sandro's Windows PC. "
        "Be concise, practical, and safe. Respect Eve's constitution and permissions. "
        "Use the local memory context as persistent background, but do not claim actions you did not perform.\n\n"
        f"LOCAL MEMORY CONTEXT:\n{memory_context}"
    )
    append_chat("user", prompt)
    body = {
        "model": model,
        "instructions": instructions,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
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
        return text
    else:
        text = json.dumps(payload, indent=2)[:4000]
        print(text)
        append_chat("assistant", text)
        return text


def chat() -> None:
    print("Eve chat. Escreve /sair para sair.")
    print("Comandos: /modelo, /estado, /ecra, /ver-texto, /mouse, /mover, /clicar, /tecla, /hotkey, /escrever, /lock, /unlock, /diario, /consolidar, /sonhar, /lembrar, /world, /tech, /lab, /workspace, /ls, /ler, /nota, /cmd, /aprovar-cmd, /erros, /skills, /skill-run, /skill-promote, /skill-demo")
    print()
    while True:
        try:
            prompt = input("tu> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not prompt:
            continue
        if prompt.lower() in {"/sair", "/exit", "exit", "quit"}:
            return
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
        if prompt.lower() == "/ecra":
            try:
                print(json.dumps(describe_screen(), indent=2, ensure_ascii=False)[:6000])
            except Exception as exc:
                print(f"Erro a observar ecra: {exc}")
            continue
        if prompt.lower().startswith("/ver-texto "):
            try:
                print(json.dumps(find_text_on_screen(prompt.split(None, 1)[1]), indent=2, ensure_ascii=False)[:6000])
            except Exception as exc:
                print(f"Erro a procurar texto no ecra: {exc}")
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
        ask(prompt)
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
    sub.add_parser("login")
    sub.add_parser("status")
    sub.add_parser("chat")
    sub.add_parser("current-model")
    sub.add_parser("models")
    ask_p = sub.add_parser("ask")
    ask_p.add_argument("prompt")
    model_p = sub.add_parser("model")
    model_p.add_argument("model")
    args = parser.parse_args()

    if args.cmd == "login":
        login()
    elif args.cmd == "status":
        status()
    elif args.cmd == "chat":
        chat()
    elif args.cmd == "current-model":
        print_model()
    elif args.cmd == "models":
        print("Modelos sugeridos:")
        for model in KNOWN_MODELS:
            print(f"  {model}")
    elif args.cmd == "ask":
        ask(args.prompt)
    elif args.cmd == "model":
        set_model(args.model)


if __name__ == "__main__":
    main()
