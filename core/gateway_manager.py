from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import EVE_ROOT, LOGS_DIR, STATE_DIR, ensure_project_dirs


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
FALLBACK_PORTS = (8788, 8798, 8799)
STATE_PATH = STATE_DIR / "gateway_state.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_ps(command: str, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=str(EVE_ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def _tcp_listening(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _port_owner(port: int = DEFAULT_PORT) -> int | None:
    try:
        completed = _run_ps(
            f"Get-NetTCPConnection -LocalPort {int(port)} -State Listen -ErrorAction SilentlyContinue | "
            "Select-Object -First 1 -ExpandProperty OwningProcess"
        )
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip().splitlines()
    if not value:
        return None
    try:
        return int(value[0].strip())
    except ValueError:
        return None


def _process_info(pid: int | None) -> dict[str, Any] | None:
    if not pid:
        return None
    try:
        completed = _run_ps(
            f"$p=Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue; "
            "if ($p) { $p | Select-Object Id,Path,StartTime | ConvertTo-Json -Compress }",
        )
    except Exception:
        return {"pid": pid}
    if completed.returncode != 0 or not completed.stdout.strip():
        return {"pid": pid}
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"pid": pid}
    return {
        "pid": data.get("Id", pid),
        "path": data.get("Path"),
        "start_time": data.get("StartTime"),
    }


def _web_gateway_processes() -> list[dict[str, Any]]:
    script = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.CommandLine -match 'app[\\\\/]eve_web\\.py' } | "
        "Select-Object ProcessId,CommandLine,CreationDate | ConvertTo-Json -Compress"
    )
    try:
        completed = _run_ps(script, timeout=15)
    except Exception:
        return []
    if completed.returncode != 0 or not completed.stdout.strip():
        return []
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    return [
        {
            "pid": item.get("ProcessId"),
            "command_line": item.get("CommandLine"),
            "creation_date": item.get("CreationDate"),
        }
        for item in data
        if isinstance(item, dict)
    ]


def _tail_file(path: Path, max_chars: int = 4000) -> str:
    try:
        if not path.exists():
            return ""
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - max_chars))
            return handle.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def http_json(path: str = "/api/health", *, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 2.0) -> dict[str, Any]:
    url = f"http://{host}:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
        return {"ok": True, "url": url, "data": json.loads(raw)}
    except Exception as exc:
        return {"ok": False, "url": url, "error": f"{type(exc).__name__}: {exc}"}


def http_text(path: str = "/", *, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 2.0) -> dict[str, Any]:
    url = f"http://{host}:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
        return {"ok": True, "url": url, "text": raw}
    except Exception as exc:
        return {"ok": False, "url": url, "error": f"{type(exc).__name__}: {exc}"}


def gateway_state(*, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, include_processes: bool = True) -> dict[str, Any]:
    ensure_project_dirs()
    listening = _tcp_listening(host, port)
    pid = _port_owner(port) if listening else None
    health = http_json("/api/health", host=host, port=port, timeout=2.0) if listening else {"ok": False, "error": "not listening"}
    page = http_text("/", host=host, port=port, timeout=2.0) if listening else {"ok": False, "error": "not listening"}
    text = page.get("text") or ""
    health_data = health.get("data") or {}
    state_pid = pid or health_data.get("pid")
    state = {
        "ok": bool(listening and health.get("ok") and page.get("ok")),
        "timestamp": _now(),
        "root": str(EVE_ROOT),
        "host": host,
        "port": port,
        "listening": listening,
        "pid": state_pid,
        "process": _process_info(state_pid),
        "web_processes": _web_gateway_processes() if include_processes else [],
        "health": health,
        "served_html_ok": bool(page.get("ok")),
        "ui_version": (health_data.get("ui_version") if health.get("ok") else None),
        "features": (health_data.get("features") if health.get("ok") else []),
        "has_image_upload": "imageInput" in text and "pickImage" in text,
        "uptime_seconds": (health_data.get("uptime_seconds") if health.get("ok") else None),
    }
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return state


def stop_gateway(*, port: int = DEFAULT_PORT) -> dict[str, Any]:
    pid = _port_owner(port) if _tcp_listening(DEFAULT_HOST, port) else None
    process_ids = {int(pid)} if pid else set()
    for process in _web_gateway_processes():
        try:
            process_ids.add(int(process.get("pid")))
        except (TypeError, ValueError):
            pass
    if not process_ids:
        return {"ok": True, "stopped": False, "reason": "not running"}
    try:
        joined = ",".join(str(item) for item in sorted(process_ids))
        _run_ps(f"Stop-Process -Id {joined} -Force -ErrorAction SilentlyContinue", timeout=10)
    except Exception as exc:
        return {"ok": False, "pids": sorted(process_ids), "error": f"{type(exc).__name__}: {exc}"}
    deadline = time.time() + 8
    while time.time() < deadline:
        if not _tcp_listening(DEFAULT_HOST, port) and not _web_gateway_processes():
            return {"ok": True, "stopped": True, "pids": sorted(process_ids)}
        time.sleep(0.25)
    return {"ok": False, "stopped": False, "pids": sorted(process_ids), "error": "gateway still present after stop"}


def _spawn_gateway_once(*, host: str, port: int, open_ui: bool) -> dict[str, Any]:
    ensure_project_dirs()
    if _tcp_listening(host, port):
        return {"ok": True, "started": False, "reason": "already running", "state": gateway_state(host=host, port=port)}
    stdout = LOGS_DIR / "eve_web_gateway.out.log"
    stderr = LOGS_DIR / "eve_web_gateway.err.log"
    args = [
        sys.executable,
        str(EVE_ROOT / "app" / "eve_web.py"),
        "--host",
        host,
        "--port",
        str(port),
    ]
    if open_ui:
        args.append("--open")
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    out_handle = stdout.open("a", encoding="utf-8")
    err_handle = stderr.open("a", encoding="utf-8")
    try:
        process = subprocess.Popen(
            args,
            cwd=str(EVE_ROOT),
            stdout=out_handle,
            stderr=err_handle,
            creationflags=creationflags,
        )
    finally:
        out_handle.close()
        err_handle.close()
    deadline = time.time() + 12
    last_state: dict[str, Any] = {}
    while time.time() < deadline:
        last_state = gateway_state(host=host, port=port, include_processes=False)
        if last_state.get("listening") and last_state.get("served_html_ok"):
            return {"ok": True, "started": True, "pid": process.pid, "state": last_state}
        time.sleep(0.5)
    try:
        process.terminate()
        process.wait(timeout=3)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
    return {
        "ok": False,
        "started": False,
        "pid": process.pid,
        "state": last_state,
        "stdout_tail": _tail_file(stdout),
        "stderr_tail": _tail_file(stderr),
        "error": "gateway did not become healthy",
    }


def start_gateway(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    open_ui: bool = False,
    allow_fallback: bool = True,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    ports = [port]
    if allow_fallback:
        ports.extend(item for item in FALLBACK_PORTS if item != port)
    for candidate_port in ports:
        attempt = _spawn_gateway_once(host=host, port=candidate_port, open_ui=open_ui)
        attempts.append(
            {
                "ok": attempt.get("ok"),
                "port": candidate_port,
                "started": attempt.get("started"),
                "pid": attempt.get("pid"),
                "reason": attempt.get("reason"),
                "error": attempt.get("error"),
            }
        )
        if attempt.get("ok"):
            result = dict(attempt)
            result["requested_port"] = port
            result["actual_port"] = candidate_port
            result["fallback_used"] = candidate_port != port
            result["attempts"] = attempts
            return result
    return {
        "ok": False,
        "started": False,
        "requested_port": port,
        "actual_port": None,
        "fallback_used": False,
        "attempts": attempts,
        "error": "no gateway port became healthy",
    }


def restart_gateway(*, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, open_ui: bool = False, require_image_upload: bool = True) -> dict[str, Any]:
    stopped = stop_gateway(port=port)
    started = start_gateway(host=host, port=port, open_ui=open_ui)
    actual_port = int(started.get("actual_port") or port)
    state = gateway_state(host=host, port=actual_port)
    verified = bool(state.get("listening") and state.get("served_html_ok"))
    if require_image_upload:
        verified = verified and bool(state.get("has_image_upload"))
    payload = {
        "ok": verified,
        "requested_port": port,
        "actual_port": actual_port,
        "fallback_used": actual_port != port,
        "stopped": stopped,
        "started": started,
        "state": state,
    }
    STATE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Eve gateway self-awareness and restart manager")
    parser.add_argument("command", choices=["state", "start", "stop", "restart"])
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    if args.command == "state":
        result = gateway_state(host=args.host, port=args.port)
    elif args.command == "start":
        result = start_gateway(host=args.host, port=args.port, open_ui=args.open)
    elif args.command == "stop":
        result = stop_gateway(port=args.port)
    else:
        result = restart_gateway(host=args.host, port=args.port, open_ui=args.open)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
