from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.paths import EVE_ROOT, LOGS_DIR, STATE_DIR
from security.secrets_vault import get_secret
from tools.telegram_bridge import TOKEN_SECRET_NAME


def _run_status() -> tuple[dict[str, Any] | None, str | None]:
    script = EVE_ROOT / "scripts" / "telegram_bridge.py"
    try:
        completed = subprocess.run(
            [sys.executable, str(script), "status"],
            cwd=str(EVE_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if completed.returncode != 0:
        return None, (completed.stderr or completed.stdout or f"returncode={completed.returncode}")[-1000:]
    try:
        start = completed.stdout.find("{")
        end = completed.stdout.rfind("}")
        return json.loads(completed.stdout[start : end + 1]), None
    except Exception as exc:
        return None, f"status parse failed: {type(exc).__name__}: {exc}"


def _secret_status() -> dict[str, Any]:
    try:
        item = get_secret(TOKEN_SECRET_NAME, reveal=False)
        return {
            "configured": True,
            "name": item.get("name"),
            "masked": item.get("masked"),
        }
    except Exception as exc:
        return {
            "configured": False,
            "name": TOKEN_SECRET_NAME,
            "masked": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def _recent_bridge_errors(limit: int = 5) -> list[dict[str, Any]]:
    path = LOGS_DIR / "telegram_bridge.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-200:]:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("event") == "bridge_error":
                rows.append(
                    {
                        "timestamp": row.get("timestamp"),
                        "error": str(row.get("error") or "")[:500],
                    }
                )
    except Exception as exc:
        return [{"timestamp": None, "error": f"could not read bridge log: {type(exc).__name__}: {exc}"}]
    return rows[-limit:]


def main() -> int:
    tools_bridge = EVE_ROOT / "tools" / "telegram_bridge.py"
    script_bridge = EVE_ROOT / "scripts" / "telegram_bridge.py"
    state_path = STATE_DIR / "telegram_bridge_state.json"
    status, status_error = _run_status()
    token = _secret_status()
    errors = _recent_bridge_errors()
    payload: dict[str, Any] = {
        "ok": bool(tools_bridge.exists() and script_bridge.exists() and token.get("configured") and status is not None),
        "repo_root": str(EVE_ROOT),
        "tools_bridge_exists": tools_bridge.exists(),
        "script_bridge_exists": script_bridge.exists(),
        "token": token,
        "running": bool((status or {}).get("running")),
        "pid": (status or {}).get("pid"),
        "last_update": (status or {}).get("last_message_at") or (status or {}).get("updated_at"),
        "state_path": str(state_path),
        "status_error": status_error,
        "errors": errors,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
