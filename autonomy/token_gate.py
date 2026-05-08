from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.paths import LOGS_DIR, ensure_project_dirs


DEFAULT_DAILY_BUDGET = 6
DEFAULT_COOLDOWN_MINUTES = 30


def _parse_time(value: str) -> datetime:
    clean = value.replace("Z", "+00:00")
    return datetime.fromisoformat(clean)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def llm_call_log_path() -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "autonomy" / "llm_calls.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_llm_call_history(limit: int = 100) -> list[dict]:
    path = llm_call_log_path()
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _calls_today(history: list[dict], now: datetime) -> list[dict]:
    return [entry for entry in history if entry.get("timestamp", "")[:10] == now.date().isoformat()]


def _in_cooldown(history: list[dict], now: datetime, cooldown_minutes: int) -> bool:
    if not history:
        return False
    latest = max((_parse_time(entry["timestamp"]) for entry in history if entry.get("timestamp")), default=None)
    if latest is None:
        return False
    return latest > now - timedelta(minutes=cooldown_minutes)


def _repeated_error_type(errors: list[dict]) -> str | None:
    counts = Counter(err.get("error_type", "unknown") for err in errors)
    for error_type, count in counts.items():
        if count >= 2:
            return error_type
    return None


def decide_llm_call(context: dict) -> dict:
    now = _parse_time(context.get("now") or now_iso())
    history = context.get("call_history")
    if history is None:
        history = load_llm_call_history()
    daily_budget = int(context.get("daily_budget", DEFAULT_DAILY_BUDGET))
    cooldown_minutes = int(context.get("cooldown_minutes", DEFAULT_COOLDOWN_MINUTES))
    impulses = context.get("impulses") or []
    errors = context.get("recent_errors") or []

    if len(_calls_today(history, now)) >= daily_budget:
        return {
            "should_call_llm": False,
            "reason": "orcamento diario de chamadas LLM atingido",
            "prompt_type": "none",
            "risk": "low",
            "budget_ok": False,
            "cooldown_ok": True,
        }
    if _in_cooldown(history, now, cooldown_minutes):
        return {
            "should_call_llm": False,
            "reason": "cooldown ativo para evitar chamadas LLM excessivas",
            "prompt_type": "none",
            "risk": "low",
            "budget_ok": True,
            "cooldown_ok": False,
        }

    repeated = _repeated_error_type(errors)
    if repeated:
        return {
            "should_call_llm": True,
            "reason": f"erro repetido sem analise profunda: {repeated}",
            "prompt_type": "error_analysis",
            "risk": "low",
            "budget_ok": True,
            "cooldown_ok": True,
        }

    if any(item.get("kind") in {"memory_hygiene", "self_review"} for item in impulses):
        return {
            "should_call_llm": True,
            "reason": "ciclo reflexivo beneficia de sintese e julgamento do LLM",
            "prompt_type": "self_reflection",
            "risk": "low",
            "budget_ok": True,
            "cooldown_ok": True,
        }

    return {
        "should_call_llm": False,
        "reason": "sem sinal suficiente para gastar tokens",
        "prompt_type": "none",
        "risk": "low",
        "budget_ok": True,
        "cooldown_ok": True,
    }


def record_llm_call(cycle_name: str, decision: dict, *, result: dict | None = None) -> Path:
    row = {
        "timestamp": now_iso(),
        "cycle": cycle_name,
        "decision": decision,
        "result": result or {},
    }
    path = llm_call_log_path()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path
