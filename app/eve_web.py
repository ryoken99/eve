from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import threading
import time
import urllib.parse
import webbrowser
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

EVE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if EVE_ROOT not in sys.path:
    sys.path.insert(0, EVE_ROOT)

from app.eve_codex import active_auth_profile, ask, list_auth_accounts, select_auth_account
from memory.daily_transcripts import append_transcript, transcript_path
from security.local_account import active_installation, list_installations, set_active_installation, verify_access_code


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
UPLOAD_DIR = Path(EVE_ROOT) / "logs" / "interface_uploads"
MAX_IMAGE_BYTES = 12 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def access_code_status(value: str) -> dict[str, Any]:
    return verify_access_code(value)


def check_access_code(value: str) -> bool:
    return bool(access_code_status(value).get("ok"))


def _safe_upload_name(value: str) -> str:
    name = Path(str(value or "image")).stem
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")
    return name[:60] or "image"


def save_chat_image(image: dict[str, Any]) -> dict[str, Any]:
    content_type = str(image.get("type") or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Formato de imagem nao suportado. Usa PNG, JPG, WEBP ou GIF.")
    data_url = str(image.get("data") or "")
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    try:
        raw = base64.b64decode(data_url, validate=True)
    except Exception as exc:
        raise ValueError("Imagem invalida ou corrompida.") from exc
    if not raw:
        raise ValueError("Imagem vazia.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("Imagem demasiado grande. Limite: 12 MB.")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    suffix = ALLOWED_IMAGE_TYPES[content_type]
    target = UPLOAD_DIR / f"{stamp}_{_safe_upload_name(str(image.get('name') or 'image'))}{suffix}"
    target.write_bytes(raw)
    return {
        "path": str(target),
        "name": str(image.get("name") or target.name),
        "content_type": content_type,
        "bytes": len(raw),
    }


def recent_activity(limit: int = 8) -> list[dict[str, Any]]:
    items: deque[dict[str, Any]] = deque(maxlen=max(1, min(int(limit or 8), 50)))
    for kind in ("actions", "tools", "errors"):
        path = transcript_path(kind)
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                row["kind"] = kind
                items.append(row)
    return sorted(items, key=lambda row: row.get("timestamp", ""))[-max(1, min(int(limit or 8), 50)):]


def recent_chat_messages(limit: int = 40) -> list[dict[str, str]]:
    items: deque[dict[str, str]] = deque(maxlen=max(1, min(int(limit or 40), 200)))
    path = transcript_path("chat")
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = row.get("payload") or {}
            content = str(payload.get("content") or "").strip()
            if not content:
                continue
            if row.get("event") in {"web_user_message", "console_user_message"}:
                items.append({"who": "user", "text": content})
            elif row.get("event") in {"web_eve_reply", "console_eve_reply"}:
                items.append({"who": "eve", "text": content})
    return list(items)


def render_index() -> str:
    return r"""<!doctype html>
<html lang="pt">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Eve</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0e1014;
      --panel: #161a21;
      --line: #2a303b;
      --text: #eef2f6;
      --muted: #9aa5b5;
      --accent: #64d2ff;
      --danger: #ff6b7a;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      font-family: Segoe UI, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    button, input, textarea, select { font: inherit; }
    .login {
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
    }
    .login-box {
      width: min(360px, 100%);
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 22px;
    }
    h1 { margin: 0 0 18px; font-size: 24px; letter-spacing: 0; }
    label { display: block; color: var(--muted); font-size: 13px; margin-bottom: 8px; }
    input, textarea, select {
      width: 100%;
      background: #0b0d11;
      color: var(--text);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 11px 12px;
      outline: none;
    }
    input:focus, textarea:focus, select:focus { border-color: var(--accent); }
    button {
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: #061018;
      padding: 10px 14px;
      cursor: pointer;
      font-weight: 600;
    }
    button.secondary {
      background: #252b35;
      color: var(--text);
      border: 1px solid var(--line);
    }
    button:disabled { opacity: .55; cursor: wait; }
    .err { color: var(--danger); min-height: 20px; margin-top: 10px; }
    .app { display: none; height: 100vh; grid-template-rows: auto 1fr auto; overflow: hidden; background: var(--bg); }
    header {
      height: 58px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 18px;
      border-bottom: 1px solid var(--line);
      background: #11151b;
    }
    .brand { font-weight: 700; }
    .account { display: flex; gap: 8px; align-items: center; }
    main {
      min-height: 0;
      overflow: auto;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .msg {
      max-width: 920px;
      white-space: pre-wrap;
      line-height: 1.45;
      padding: 12px 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }
    .msg.user { align-self: flex-end; background: #102330; border-color: #21485e; }
    .msg.eve { align-self: flex-start; }
    .composer {
      border-top: 1px solid var(--line);
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 10px;
      padding: 14px;
      background: #11151b;
      min-height: 80px;
      align-items: end;
    }
    .attach-wrap { display: grid; gap: 6px; align-content: end; }
    .attach-wrap input { display: none; }
    .attach-name { color: var(--muted); font-size: 12px; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .activity {
      min-height: 22px;
      max-height: 68px;
      overflow: auto;
      border-top: 1px solid var(--line);
      padding: 6px 14px;
      color: var(--muted);
      font-size: 12px;
      background: #0f1319;
      white-space: pre-wrap;
    }
    textarea {
      min-height: 48px;
      max-height: 160px;
      resize: vertical;
    }
    dialog {
      background: var(--panel);
      color: var(--text);
      border: 1px solid var(--line);
      border-radius: 8px;
      width: min(420px, calc(100% - 28px));
    }
    dialog::backdrop { background: rgba(0,0,0,.55); }
    .row { display: grid; gap: 10px; margin: 12px 0; }
    .status { color: var(--muted); font-size: 13px; }
  </style>
</head>
<body>
  <section class="login" id="login">
    <div class="login-box">
      <h1>Eve</h1>
      <label for="code">Código de entrada</label>
      <input id="code" type="password" autocomplete="current-password" inputmode="numeric" />
      <div class="row" id="installChoice" style="display:none">
        <label for="installations">Perfil deste PC</label>
        <select id="installations"></select>
        <button id="useInstallation" type="button">Usar perfil</button>
      </div>
      <div style="height:12px"></div>
      <button id="enter">Entrar</button>
      <div class="err" id="loginErr"></div>
    </div>
  </section>

  <section class="app" id="app">
    <header>
      <div>
        <div class="brand">Eve</div>
        <div class="status" id="status">Local</div>
      </div>
      <div class="account">
        <span class="status" id="activeAccount"></span>
        <button class="secondary" id="accountBtn">Conta</button>
      </div>
    </header>
    <main id="messages"></main>
    <div class="activity" id="activity">Ações da Eve aparecem aqui.</div>
    <form class="composer" id="form">
      <div class="attach-wrap">
        <button class="secondary" id="pickImage" type="button">Imagem</button>
        <input id="imageInput" type="file" accept="image/*" />
        <div class="attach-name" id="imageName"></div>
      </div>
      <textarea id="message" placeholder="Escreve para a Eve..."></textarea>
      <button id="send" type="submit">Enviar</button>
    </form>
  </section>

  <dialog id="accountDialog">
    <h1>Conta Codex</h1>
    <div class="row">
      <select id="accounts"></select>
      <button id="useAccount">Trocar conta</button>
      <button class="secondary" id="closeAccount">Fechar</button>
    </div>
    <div class="status" id="accountStatus"></div>
  </dialog>

  <script>
    const login = document.getElementById('login');
    const app = document.getElementById('app');
    const code = document.getElementById('code');
    const loginErr = document.getElementById('loginErr');
    const installChoice = document.getElementById('installChoice');
    const installations = document.getElementById('installations');
    const messages = document.getElementById('messages');
    const form = document.getElementById('form');
    const message = document.getElementById('message');
    const imageInput = document.getElementById('imageInput');
    const imageName = document.getElementById('imageName');
    const send = document.getElementById('send');
    const statusEl = document.getElementById('status');
    const activity = document.getElementById('activity');
    const activeAccount = document.getElementById('activeAccount');
    const accountDialog = document.getElementById('accountDialog');
    const accounts = document.getElementById('accounts');
    const accountStatus = document.getElementById('accountStatus');

    function showApp() {
      login.style.display = 'none';
      app.style.display = 'grid';
      loadAccounts();
      loadRecentChat();
      message.focus();
    }
    function renderInstallations(rows) {
      installations.innerHTML = '';
      (rows || []).forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.name;
        const flags = [];
        if (item.current_root) flags.push('nesta pasta');
        if (!item.exists) flags.push('pasta ausente');
        opt.textContent = item.label + ' - ' + item.root + (flags.length ? ' (' + flags.join(', ') + ')' : '');
        installations.appendChild(opt);
      });
      installChoice.style.display = installations.children.length ? 'grid' : 'none';
    }
    function addMsg(who, text) {
      const div = document.createElement('div');
      div.className = 'msg ' + who;
      div.textContent = text;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }
    function readImageFile(file) {
      return new Promise((resolve, reject) => {
        if (!file) return resolve(null);
        if (!file.type || !file.type.startsWith('image/')) return reject(new Error('Escolhe uma imagem.'));
        const reader = new FileReader();
        reader.onload = () => resolve({name: file.name, type: file.type, size: file.size, data: reader.result});
        reader.onerror = () => reject(new Error('Nao consegui ler a imagem.'));
        reader.readAsDataURL(file);
      });
    }
    function renderActivity(rows) {
      if (!rows || !rows.length) return;
      activity.textContent = rows.map(row => {
        const p = row.payload || {};
        if (row.event === 'tool_start') return 'chama ' + p.tool + ' tentativa ' + p.attempt;
        if (row.event === 'tool_verification') return 'verifica ' + p.tool + ': ' + ((p.verification || {}).status || '');
        if (row.event === 'tool_result') return 'resultado ' + p.tool;
        if (row.event === 'tool_verification_failed') return 'falha ' + p.tool;
        if (row.event === 'web_error') return 'erro web: ' + (p.error || '');
        return row.event;
      }).join('\n');
    }
    async function pollActivity() {
      if (app.style.display !== 'grid') return;
      try {
        const res = await fetch('/api/activity?limit=8');
        const data = await res.json();
        if (data.ok) renderActivity(data.items);
      } catch (_) {}
    }
    setInterval(pollActivity, 1500);
    document.getElementById('pickImage').onclick = () => imageInput.click();
    imageInput.onchange = () => {
      const file = imageInput.files && imageInput.files[0];
      imageName.textContent = file ? file.name : '';
    };
    async function api(path, payload) {
      const res = await fetch(path, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload || {})
      });
      const data = await res.json();
      if (!res.ok || data.ok === false) throw new Error(data.error || 'Erro');
      return data;
    }
    async function loadAccounts() {
      const res = await fetch('/api/accounts');
      const data = await res.json();
      activeAccount.textContent = data.active ? 'Conta: ' + data.active : 'Sem conta';
      accounts.innerHTML = '';
      data.accounts.forEach(acc => {
        const opt = document.createElement('option');
        opt.value = acc.profile;
        opt.textContent = (acc.active ? '* ' : '') + acc.profile;
        accounts.appendChild(opt);
      });
    }
    async function loadRecentChat() {
      try {
        const res = await fetch('/api/recent-chat?limit=40');
        const data = await res.json();
        if (!data.ok || !data.items || !data.items.length || messages.children.length) return;
        data.items.forEach(item => addMsg(item.who, item.text));
      } catch (_) {}
    }
    document.getElementById('enter').onclick = async () => {
      loginErr.textContent = '';
      try {
        const data = await api('/api/login', {code: code.value});
        if (data.requires_installation_choice) {
          renderInstallations(data.installations);
          loginErr.textContent = 'Escolhe se esta sessao e PC 1, PC 2 ou outro perfil local.';
          return;
        }
        localStorage.setItem('eve_access', '1');
        showApp();
      } catch (err) {
        loginErr.textContent = 'Código inválido.';
      }
    };
    document.getElementById('useInstallation').onclick = async () => {
      loginErr.textContent = '';
      try {
        const data = await api('/api/use-installation', {name: installations.value});
        if (!data.matches_current_root) {
          loginErr.textContent = 'Perfil ativo aponta para ' + data.root + '. Abre a Eve a partir dessa pasta para mudar de PC.';
          return;
        }
        localStorage.setItem('eve_access', '1');
        showApp();
      } catch (err) {
        loginErr.textContent = err.message;
      }
    };
    code.addEventListener('keydown', ev => { if (ev.key === 'Enter') document.getElementById('enter').click(); });
    form.onsubmit = async ev => {
      ev.preventDefault();
      const text = message.value.trim();
      const file = imageInput.files && imageInput.files[0];
      if (!text && !file) return;
      message.value = '';
      imageName.textContent = '';
      addMsg('user', text || '[imagem]');
      send.disabled = true;
      statusEl.textContent = 'Eve está a trabalhar...';
      try {
        const image = await readImageFile(file);
        imageInput.value = '';
        const data = await api('/api/chat', {message: text, image});
        addMsg('eve', data.reply || '');
      } catch (err) {
        addMsg('eve', 'Erro: ' + err.message);
      } finally {
        send.disabled = false;
        statusEl.textContent = 'Local';
        message.focus();
      }
    };
    document.getElementById('accountBtn').onclick = async () => {
      accountStatus.textContent = '';
      await loadAccounts();
      accountDialog.showModal();
    };
    document.getElementById('closeAccount').onclick = () => accountDialog.close();
    document.getElementById('useAccount').onclick = async () => {
      accountStatus.textContent = '';
      try {
        const data = await api('/api/use-account', {profile: accounts.value});
        accountStatus.textContent = 'Conta ativa: ' + data.active;
        await loadAccounts();
      } catch (err) {
        accountStatus.textContent = err.message;
      }
    };
    if (localStorage.getItem('eve_access') === '1') showApp();
  </script>
</body>
</html>"""


class EveWebHandler(BaseHTTPRequestHandler):
    server_version = "EveWeb/1.0"

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            body = render_index().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/accounts":
            accounts = list_auth_accounts()
            self._send_json({"ok": True, "active": active_auth_profile(), "accounts": accounts})
            return
        if parsed.path == "/api/installations":
            self._send_json({"ok": True, "active": active_installation(), "installations": list_installations()})
            return
        if parsed.path == "/api/activity":
            query = urllib.parse.parse_qs(parsed.query)
            limit = int((query.get("limit") or ["8"])[0])
            self._send_json({"ok": True, "items": recent_activity(limit)})
            return
        if parsed.path == "/api/recent-chat":
            query = urllib.parse.parse_qs(parsed.query)
            limit = int((query.get("limit") or ["40"])[0])
            self._send_json({"ok": True, "items": recent_chat_messages(limit)})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        data = self._read_json()
        try:
            if parsed.path == "/api/login":
                result = access_code_status(str(data.get("code") or ""))
                ok = bool(result.get("ok"))
                installations = result.get("installations") or []
                requires_choice = ok and len(installations) > 1
                append_transcript("actions", "web_login", {"ok": ok, "requires_installation_choice": requires_choice})
                self._send_json({
                    "ok": ok,
                    "requires_installation_choice": requires_choice,
                    "installations": installations,
                    "active_installation": result.get("active_installation"),
                }, 200 if ok else 403)
                return
            if parsed.path == "/api/use-installation":
                result = set_active_installation(str(data.get("name") or ""))
                append_transcript("actions", "web_installation_switch", result)
                self._send_json(result)
                return
            if parsed.path == "/api/use-account":
                profile = str(data.get("profile") or "")
                select_auth_account(profile)
                append_transcript("actions", "web_account_switch", {"profile": profile})
                self._send_json({"ok": True, "active": active_auth_profile()})
                return
            if parsed.path == "/api/chat":
                text = str(data.get("message") or "").strip()
                image_meta = None
                if data.get("image"):
                    image_meta = save_chat_image(data.get("image") or {})
                if not text and not image_meta:
                    self._send_json({"ok": False, "error": "Mensagem vazia."}, 400)
                    return
                prompt = text
                if image_meta:
                    image_note = (
                        "\n\n[Imagem enviada pelo Sandro]\n"
                        f"- Ficheiro local: {image_meta['path']}\n"
                        f"- Nome original: {image_meta['name']}\n"
                        f"- Tipo: {image_meta['content_type']}\n"
                        f"- Bytes: {image_meta['bytes']}\n"
                        "Usa este caminho local para analisar a imagem com as tuas ferramentas de visao/OCR quando necessario."
                    )
                    prompt = (prompt or "Analisa esta imagem.") + image_note
                append_transcript("chat", "web_user_message", {"content": text or "[imagem]", "image": image_meta})
                reply = ask(prompt, speaker="sandro", publish_to_interface=False)
                append_transcript("chat", "web_eve_reply", {"content": reply})
                self._send_json({"ok": True, "reply": reply, "image": image_meta})
                return
        except Exception as exc:
            append_transcript("errors", "web_error", {"path": parsed.path, "error": f"{type(exc).__name__}: {exc}"})
            self._send_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, 500)
            return
        except SystemExit as exc:
            message = str(exc) or "A operacao foi interrompida."
            append_transcript("errors", "web_system_exit", {"path": parsed.path, "error": message})
            self._send_json({"ok": False, "error": message}, 500)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: Any) -> None:
        append_transcript("actions", "web_request", {"client": self.address_string(), "message": format % args})


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, *, open_ui: bool = False) -> None:
    url = f"http://{host}:{port}/"
    if open_ui:
        threading.Thread(target=lambda: (time.sleep(1), webbrowser.open(url)), daemon=True).start()
    server = ThreadingHTTPServer((host, port), EveWebHandler)
    print(f"Eve web interface: {url}")
    append_transcript("actions", "web_server_started", {"url": url})
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Eve local web interface")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    try:
        run_server(args.host, args.port, open_ui=args.open)
    except OSError:
        url = f"http://{args.host}:{args.port}/"
        if args.open:
            webbrowser.open(url)
        print(f"Eve web interface already running or port unavailable: {url}")


if __name__ == "__main__":
    main()
