from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.paths import EVE_ROOT, LOGS_DIR, STATE_DIR, ensure_project_dirs
from core.telegram_memory_context import build_telegram_prompt
from core.transcript_writer import write_transcript
from core.memory_retrieval import COLLECTIONS, get_collection, load_vector_manifest
from memory.daily_transcripts import append_transcript
from local_embedding_provider import check_ollama_embedding_model
from security.secrets_vault import get_secret, mask_secret


TOKEN_SECRET_NAME = "telegram_eveh_by_r_bot_token"
STATE_PATH = STATE_DIR / "telegram_bridge_state.json"
PID_PATH = STATE_DIR / "telegram_bridge.pid"
LOG_PATH = LOGS_DIR / "telegram_bridge.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_state() -> dict[str, Any]:
    ensure_project_dirs()
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict[str, Any]) -> dict[str, Any]:
    ensure_project_dirs()
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return state


def _log(event: str, payload: dict[str, Any]) -> None:
    ensure_project_dirs()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {"timestamp": now_iso(), "event": event, **payload}
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    append_transcript("actions", f"telegram_{event}", payload)


def telegram_token(secret_name: str = TOKEN_SECRET_NAME) -> str:
    return str(get_secret(secret_name, reveal=True)["value"])


def telegram_api(method: str, params: dict[str, Any] | None = None, *, token: str | None = None, timeout: int = 30) -> dict[str, Any]:
    token = token or telegram_token()
    encoded = urllib.parse.urlencode(params or {}).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=encoded,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API {method} failed: {payload}")
    return payload


def send_message(chat_id: int | str, text: str, *, token: str | None = None) -> dict[str, Any]:
    payload = telegram_api("sendMessage", {"chat_id": str(chat_id), "text": text[:3900]}, token=token)
    result = payload.get("result") or {}
    _log("send_message", {"chat_id": chat_id, "message_id": result.get("message_id"), "text_preview": text[:120]})
    return {"ok": True, "chat_id": chat_id, "message_id": result.get("message_id"), "text": result.get("text")}


def get_updates(*, offset: int | None = None, timeout_seconds: int = 0, token: str | None = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"timeout": int(timeout_seconds), "allowed_updates": json.dumps(["message"])}
    if offset is not None:
        params["offset"] = int(offset)
    payload = telegram_api("getUpdates", params, token=token, timeout=max(10, timeout_seconds + 5))
    return list(payload.get("result") or [])


def _extract_message(update: dict[str, Any]) -> dict[str, Any] | None:
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    text = str(message.get("text") or "").strip()
    if not chat.get("id") or not text:
        return None
    return {
        "update_id": int(update.get("update_id")),
        "chat_id": chat.get("id"),
        "from": message.get("from") or {},
        "message_id": message.get("message_id"),
        "text": text,
    }


def _build_prompt(message: dict[str, Any]) -> str:
    sender = message.get("from") or {}
    sender_name = " ".join(str(sender.get(key) or "").strip() for key in ("first_name", "last_name")).strip()
    if not sender_name:
        sender_name = str(sender.get("username") or "Telegram")
    return (
        "[Mensagem recebida pelo Telegram]\n"
        "Contrato do canal: responde em texto normal para o Sandro. Nao chames telegram_send_message, "
        "telegram_poll_once, telegram_start_bridge nem outras ferramentas Telegram; esta ponte envia a tua resposta de volta automaticamente.\n"
        f"Origem: {sender_name}\n"
        f"Chat ID: {message.get('chat_id')}\n"
        f"Mensagem:\n{message.get('text')}"
    )


def _memory_status_text() -> str:
    manifest = load_vector_manifest()
    ollama = check_ollama_embedding_model()
    identity_ok = False
    all_count = None
    identity_count = None
    error = None
    try:
        all_count = get_collection(COLLECTIONS["all"]).count()
        identity_count = get_collection(COLLECTIONS["identity"]).count()
        identity_ok = bool(identity_count and identity_count > 0)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    lines = [
        "Memory status:",
        f"- vector DB: {'ok' if manifest.get('ok') else 'fail'}",
        f"- embedding model: nomic-embed-text ({'ok' if ollama.get('ok') else 'fail'})",
        f"- chunks indexed approx: {all_count if all_count is not None else 'unknown'}",
        f"- identity cards: {'ok' if identity_ok else 'fail'} ({identity_count if identity_count is not None else 'unknown'})",
    ]
    if error:
        lines.append(f"- last memory error: {error[:300]}")
    elif not manifest.get("ok"):
        lines.append(f"- last memory error: {manifest.get('error')}")
    return "\n".join(lines)


def _telegram_transcript_metadata(message: dict[str, Any], *, memory_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    memory_metadata = (memory_payload or {}).get("retrieval_metadata") or {}
    return {
        "telegram_chat_id": message.get("chat_id"),
        "telegram_message_id": message.get("message_id"),
        "telegram_update_id": message.get("update_id"),
        "source": "telegram_bridge",
        "memory_used": bool(memory_payload and not memory_metadata.get("fallback_without_memory")),
        "chunks_used": memory_metadata.get("chunks_used", 0),
        "memory_context_chars": memory_metadata.get("chars_used", 0),
        "memory_sources": memory_metadata.get("sources", [])[:8],
    }


def poll_once(*, respond: bool = True, token: str | None = None) -> dict[str, Any]:
    state = _load_state()
    offset = state.get("offset")
    updates = get_updates(offset=int(offset) if offset is not None else None, timeout_seconds=0, token=token)
    processed: list[dict[str, Any]] = []
    for update in updates:
        update_id = int(update.get("update_id"))
        state["offset"] = max(int(state.get("offset") or 0), update_id + 1)
        message = _extract_message(update)
        if not message:
            continue
        state["last_chat_id"] = message["chat_id"]
        state["last_message_at"] = now_iso()
        append_transcript("chat", "telegram_user_message", {"content": message["text"], "chat_id": message["chat_id"]})
        raw_text = str(message["text"] or "").strip()
        if raw_text == "/memory_status":
            reply = _memory_status_text()
            write_transcript("telegram", "sandro", raw_text, _telegram_transcript_metadata(message, memory_payload=None))
            write_transcript(
                "telegram",
                "eve",
                reply,
                {
                    "telegram_chat_id": message.get("chat_id"),
                    "telegram_message_id": None,
                    "source": "telegram_bridge",
                    "command": "memory_status",
                    "memory_used": False,
                    "chunks_used": 0,
                    "memory_context_chars": 0,
                },
            )
            if respond:
                send_message(message["chat_id"], reply, token=token)
            processed.append({"update_id": update_id, "chat_id": message["chat_id"], "responded": bool(respond), "command": "memory_status"})
            continue
        reply = ""
        if respond:
            from app.eve_codex import ask

            # The bridge owns Telegram delivery, but Eve should still have the
            # same local tool loop as the web UI for files, memory, diagnostics,
            # and other guarded actions. Hide/block Telegram transport tools so
            # the response is sent exactly once by this bridge.
            memory_payload = None
            try:
                memory_payload = build_telegram_prompt(message["text"], {"chat_id": message.get("chat_id"), "message_id": message.get("message_id")})
            except Exception as exc:
                _log("memory_retrieval_failed_telegram", {"error": f"{type(exc).__name__}: {exc}", "chat_id": message.get("chat_id")})
                memory_payload = {
                    "final_prompt": (
                        "[TELEGRAM USER MESSAGE]\n"
                        f"{message['text']}\n"
                        "[/TELEGRAM USER MESSAGE]"
                    ),
                    "retrieval_metadata": {"fallback_without_memory": True, "error": f"{type(exc).__name__}: {exc}", "chunks_used": 0, "chars_used": 0, "sources": []},
                }
            write_transcript("telegram", "sandro", message["text"], _telegram_transcript_metadata(message, memory_payload=memory_payload))
            channel_prompt = _build_prompt(message) + "\n\n" + memory_payload["final_prompt"]
            reply = ask(
                message["text"],
                speaker="sandro",
                publish_to_interface=True,
                allow_tools=True,
                visible_prompt_override=channel_prompt,
                excluded_tools={
                    "telegram_status",
                    "telegram_start_bridge",
                    "telegram_stop_bridge",
                    "telegram_poll_once",
                    "telegram_send_message",
                },
            )
            write_transcript("telegram", "eve", reply, _telegram_transcript_metadata(message, memory_payload=memory_payload))
            send_message(message["chat_id"], reply, token=token)
            append_transcript("chat", "telegram_eve_reply", {"content": reply, "chat_id": message["chat_id"]})
        processed.append({"update_id": update_id, "chat_id": message["chat_id"], "responded": bool(reply)})
    state["updated_at"] = now_iso()
    _save_state(state)
    return {"ok": True, "processed": processed, "count": len(processed), "state": public_status()}


def _pid_running(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", f"(Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue) -ne $null"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return "True" in completed.stdout
    except Exception:
        return False


def public_status() -> dict[str, Any]:
    state = _load_state()
    pid = None
    if PID_PATH.exists():
        try:
            pid = int(PID_PATH.read_text(encoding="utf-8").strip())
        except Exception:
            pid = None
    token_info: dict[str, Any]
    try:
        token_info = {"configured": True, "masked": mask_secret(telegram_token())}
    except Exception:
        token_info = {"configured": False, "masked": ""}
    return {
        "ok": True,
        "running": _pid_running(pid),
        "pid": pid,
        "token": token_info,
        "offset": state.get("offset"),
        "last_chat_id": state.get("last_chat_id"),
        "last_message_at": state.get("last_message_at"),
        "state_path": str(STATE_PATH),
    }


def start_bridge(*, interval: int = 5) -> dict[str, Any]:
    status = public_status()
    if status.get("running"):
        return {"ok": True, "started": False, "reason": "already running", "status": status}
    ensure_project_dirs()
    out = (LOGS_DIR / "telegram_bridge.out.log").open("a", encoding="utf-8")
    err = (LOGS_DIR / "telegram_bridge.err.log").open("a", encoding="utf-8")
    try:
        process = subprocess.Popen(
            [sys.executable, str(EVE_ROOT / "scripts" / "telegram_bridge.py"), "run", "--interval", str(interval)],
            cwd=str(EVE_ROOT),
            stdout=out,
            stderr=err,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    finally:
        out.close()
        err.close()
    PID_PATH.write_text(str(process.pid), encoding="utf-8")
    state = _load_state()
    state.update({"pid": process.pid, "started_at": now_iso(), "interval": interval})
    _save_state(state)
    _log("bridge_started", {"pid": process.pid, "interval": interval})
    return {"ok": True, "started": True, "pid": process.pid, "status": public_status()}


def stop_bridge() -> dict[str, Any]:
    status = public_status()
    pid = status.get("pid")
    if not pid or not status.get("running"):
        return {"ok": True, "stopped": False, "reason": "not running", "status": status}
    subprocess.run(["powershell.exe", "-NoProfile", "-Command", f"Stop-Process -Id {int(pid)} -Force -ErrorAction SilentlyContinue"], timeout=15)
    _log("bridge_stopped", {"pid": pid})
    return {"ok": True, "stopped": True, "pid": pid, "status": public_status()}


def run_loop(*, interval: int = 5) -> None:
    PID_PATH.write_text(str(os.getpid()), encoding="utf-8")
    _log("bridge_loop_started", {"pid": os.getpid(), "interval": interval})
    while True:
        try:
            poll_once(respond=True)
        except Exception as exc:
            _log("bridge_error", {"error": f"{type(exc).__name__}: {exc}"})
        time.sleep(max(1, int(interval)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Eve Telegram bridge")
    parser.add_argument("command", choices=["status", "start", "stop", "poll-once", "send", "run"])
    parser.add_argument("--interval", type=int, default=5)
    parser.add_argument("--chat-id", default="")
    parser.add_argument("--text", default="")
    args = parser.parse_args()
    if args.command == "status":
        result = public_status()
    elif args.command == "start":
        result = start_bridge(interval=args.interval)
    elif args.command == "stop":
        result = stop_bridge()
    elif args.command == "poll-once":
        result = poll_once(respond=True)
    elif args.command == "send":
        chat_id = args.chat_id or _load_state().get("last_chat_id")
        if not chat_id:
            raise SystemExit("No chat id known yet.")
        result = send_message(chat_id, args.text or "Eve Telegram bridge test")
    else:
        run_loop(interval=args.interval)
        return 0
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
