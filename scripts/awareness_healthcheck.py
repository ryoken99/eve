from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.awareness_engine import build_self_state


HEALTH_PATH = ROOT / "memory" / "runtime" / "awareness" / "health" / "latest_healthcheck.json"


def main() -> int:
    state = build_self_state()
    disk = shutil.disk_usage(str(ROOT))
    components = {
        "webui": {"ok": bool(state.get("health_summary", {}).get("webui_ok"))},
        "telegram": {"ok": bool(state.get("health_summary", {}).get("telegram_running"))},
        "ollama": {"ok": bool(state.get("health_summary", {}).get("ollama_ok"))},
        "vector_db": {"ok": bool((state.get("vector") or {}).get("chroma_exists"))},
        "memory_rollover": {"ok": bool(((state.get("rollover") or {}).get("last_rollover") or {}).get("rollup", {}).get("exists"))},
        "session_handoff": {"ok": bool(((state.get("session") or {}).get("latest_handoff") or {}).get("exists"))},
        "disk": {"ok": disk.free > 2_000_000_000, "free_bytes": disk.free},
        "git": {"ok": True, "dirty": bool((state.get("git") or {}).get("dirty"))},
        "errors": {"ok": (state.get("errors") or {}).get("open_errors", 0) is not None, "open_errors": (state.get("errors") or {}).get("open_errors")},
    }
    overall = "ok"
    if any(not item.get("ok") for key, item in components.items() if key not in {"git", "errors"}):
        overall = "fail"
    elif components["git"].get("dirty") or (components["errors"].get("open_errors") or 0) > 0:
        overall = "warning"
    result = {"overall_status": overall, "components": components, "timestamp": state.get("timestamp")}
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    HEALTH_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if overall in {"ok", "warning"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
