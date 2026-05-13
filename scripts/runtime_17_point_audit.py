from __future__ import annotations

import importlib.util
import json
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autonomy.autonomy_budget import budget_allows
from autonomy.priority_engine import score_mission
from computer.environment_state import capture_environment_state
from computer.state_diff import verify_action
from computer.uia_observer import dump_active_window_tree, uia_available
from core.awareness_engine import collect_awareness
from core.paths import LOGS_DIR, MEMORY_DIR, STATE_DIR, ensure_project_dirs
from dream.consolidation_pipeline import consolidate_diary_text
from dream.dream_evaluator import evaluate_dream
from dream.dream_synthesizer import synthesize_dream
from lab.comparison_runner import run_comparison
from lab.experiment_scheduler import schedule_experiment
from learning.error_to_test import propose_regression_test
from memory.learning_validator import validate_target_folder
from memory.memory_lifecycle import register_memory, promote_memory, expire_memory
from memory.semantic_vector.embedding_store import _hash_embedding, add_embedded_document, embedding_backend
from memory.semantic_vector.reranker import semantic_search
from memory.transcript_validator import validate_transcript_chain
from personality.preference_lifecycle import update_preference
from research.research_quality import score_research_item
from research.research_to_lab import research_to_lab_candidate
from research.runtime_research_probe import run_runtime_research_probe
from security.admin_session import create_admin_session, expire_admin_session, validate_admin_session
from security.app_permissions import check_app_permission
from self_improvement.arsi_cycle import run_arsi_cycle
from self_improvement.arsi_policy import arsi_change_allowed, arsi_policy_summary
from tools.admin_executor import admin_status, run_admin_command
from tools.browser_playwright import browser_dom_snapshot, playwright_available
from computer.ocr import ocr_status


REPORT_JSON = LOGS_DIR / "capability_runs" / "runtime_17_point_audit_latest.json"
REPORT_MD = MEMORY_DIR / "medium_term" / "runtime_17_point_audit_latest.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def _run(command: list[str], timeout: int = 60) -> dict:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return {"returncode": completed.returncode, "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]}


def _playwright_dom_smoke() -> dict:
    if not playwright_available():
        return {"ok": False, "reason": "playwright package unavailable"}
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<main><button>Save</button><label>Email<input value='eve'></label></main>")
            snapshot = browser_dom_snapshot(page)
            page.get_by_role("button", name="Save").click()
            browser.close()
        return {"ok": bool(snapshot.get("ok") and "Save" in snapshot.get("text", "")), "snapshot": snapshot}
    except Exception as exc:
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}


def _score(base: float, checks: list[tuple[str, bool, float]], limitations: list[str]) -> tuple[float, list[str]]:
    evidence = []
    score = base
    for label, ok, weight in checks:
        if ok:
            score += weight
            evidence.append(label)
        else:
            limitations.append(f"falhou: {label}")
    return round(max(0.0, min(10.0, score)), 1), evidence


def audit() -> dict:
    ensure_project_dirs()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    points = []

    # Shared probes.
    web_alive = _port_open("127.0.0.1", 8787)
    awareness = collect_awareness()
    env = capture_environment_state(include_screen=False)
    daemon_heartbeat = STATE_DIR / "daemon_heartbeat.json"
    heartbeat = json.loads(daemon_heartbeat.read_text(encoding="utf-8")) if daemon_heartbeat.exists() else {}
    cron_errors = []
    for item in (heartbeat.get("cron") or {}).get("executed", []):
        result = item.get("result") or {}
        if result.get("returncode") not in (0, None):
            cron_errors.append({"name": (item.get("job") or {}).get("name"), "returncode": result.get("returncode"), "stderr": result.get("stderr")})
        if "Cannot find path 'D:\\Eve'" in str(result.get("stderr")):
            cron_errors.append({"name": (item.get("job") or {}).get("name"), "path_error": "D:\\Eve stale path"})
    deps = {
        "pytest": _module("pytest"),
        "pyautogui": _module("pyautogui"),
        "pytesseract": _module("pytesseract"),
        "cv2": _module("cv2"),
        "pynput": _module("pynput"),
        "uiautomation": _module("uiautomation"),
        "playwright": playwright_available(),
    }
    ocr = ocr_status()
    playwright_smoke = _playwright_dom_smoke()

    def add(pid: int, title: str, base: float, checks: list[tuple[str, bool, float]], limitations: list[str] | None = None, extra: dict | None = None):
        limitations = limitations or []
        score, evidence = _score(base, checks, limitations)
        points.append({"id": pid, "title": title, "score": score, "evidence": evidence, "limitations": limitations, "extra": extra or {}})

    session = create_admin_session("runtime audit", 5, ["Get-Process*"])
    dry = run_admin_command("Get-Process python", "runtime audit dry-run", approved=True, session_id=session["session_id"], dry_run=True)
    blocked = validate_admin_session(session["session_id"], "Remove-Item x")
    expire_admin_session(session["session_id"])
    admin = admin_status()
    add(1, "Permissoes elevadas/admin", 5.8, [
        ("admin status callable", bool(admin), 0.6),
        ("admin session temporaria criada", bool(session.get("session_id")), 0.9),
        ("allowlist permite comando esperado", dry.get("allowed", False), 0.8),
        ("allowlist bloqueia comando perigoso", not blocked.get("allowed", True), 0.9),
        ("processo atual esta elevado", admin.get("is_admin_process", False), 0.9),
    ], ["processo nao esta elevado neste runtime" if not admin.get("is_admin_process") else ""], {"admin": admin})

    transcript = validate_transcript_chain("chat")
    add(2, "Diario completo das conversas", 7.4, [
        ("transcript chat validavel", "valid" in transcript, 0.5),
        ("hash chain implementada", transcript.get("valid", False) or bool(transcript.get("errors")), 0.7),
        ("canais transcript existem", all((LOGS_DIR / "transcripts" / kind).exists() for kind in ("chat", "tools", "actions", "errors", "console", "interface")), 0.8),
    ], ["hash chain antiga pode marcar entradas pre-existentes sem hash"], {"chat_transcript": transcript})

    consolidated = consolidate_diary_text("Decidi testar.\nTarefa rever.\nGosto de memoria.\nMas ha conflito.")
    add(3, "Consolidacao diaria varias vezes por dia", 6.7, [
        ("daemon heartbeat existe", daemon_heartbeat.exists(), 0.7),
        ("consolidation parser extrai categorias", all(consolidated[key] for key in ("decisions", "tasks", "preferences", "contradictions")), 0.9),
        ("cron executou sem erros", not cron_errors, 0.8),
        ("schedule 6h presente", "diary_consolidation_schedule" in str(heartbeat), 0.5),
    ], ["cron teve falhas recentes" if cron_errors else ""], {"cron_errors": cron_errors})

    mem = register_memory("runtime audit memory", source="runtime", confidence=0.8)
    promoted = promote_memory(mem["id"])
    expired = expire_memory(mem["id"])
    add(4, "Memoria curta/media/longa", 7.2, [
        ("camadas existem", all((MEMORY_DIR / name).exists() for name in ("short_term", "medium_term", "long_term")), 0.6),
        ("memoria registra metadata", bool(mem.get("created_at")), 0.5),
        ("promocao funciona", promoted.get("layer") == "medium_term", 0.6),
        ("expiracao/arquivo funciona", expired.get("status") == "archived", 0.5),
    ])

    add_embedded_document("runtime-audit", "Eve semantic memory links agents, UI automation, and Sandro projects.", {"importance": 1.0, "recency": 1.0})
    semantic = semantic_search("automation memory projects", limit=1)
    backend = embedding_backend()
    add(5, "Memoria semantica/vectorial", 5.9, [
        ("indice semantico responde", bool(semantic), 0.8),
        ("chunk/metadata disponivel", bool(semantic and semantic[0].get("metadata") is not None), 0.5),
        ("fallback local disponivel", bool(_hash_embedding("fallback probe")), 0.4),
        ("backend embeddings neural real disponivel", backend != "local-hash-embedding", 1.2),
    ], ["backend atual nao e embedding neural real" if backend == "local-hash-embedding" else ""], {"backend": backend})

    dream = synthesize_dream({"diary": ["agent memory"], "errors": ["memory error"], "research": ["agent paper"]})
    dream_score = evaluate_dream(dream)
    add(6, "Sistema de sonhos", 6.6, [
        ("sonho multi-fonte cria ligacoes", bool(dream["new_connections"]), 0.8),
        ("sonho gera lab candidates", bool(dream["lab_candidates"]), 0.5),
        ("avaliador de sonho pontua qualidade", dream_score["confidence_score"] > 0, 0.5),
        ("dream reports existem", (MEMORY_DIR / "dream_reports").exists(), 0.4),
    ])

    uia = dump_active_window_tree()
    add(7, "Awareness temporal/situacional/espacial", 6.2, [
        ("awareness coleta hora/sistema", bool(awareness.get("timestamp") and awareness.get("system")), 0.7),
        ("active window observado", "active_window" in awareness.get("desktop", {}), 0.5),
        ("environment_state captura browser/uia", "browser" in env and "uia" in env, 0.5),
        ("UI Automation real disponivel", uia_available() and uia.get("available", False), 1.0),
    ], ["uiautomation nao instalado/nao disponivel" if not uia_available() else ""], {"dependencies": deps, "uia": uia})

    topic = f"runtime preference {datetime.now().timestamp()}"
    p1 = update_preference(topic, "first", source="runtime")
    p2 = update_preference(topic, "second", source="runtime")
    p3 = update_preference(topic, "third", source="runtime")
    add(8, "Vontade/gostos/personalidade evolutiva", 6.9, [
        ("preferencia inicia candidate", p1["status"] == "candidate", 0.4),
        ("preferencia reforca", p2["status"] == "reinforced", 0.4),
        ("preferencia estabiliza por evidencia", p3["status"] == "stable", 0.5),
        ("memoria personality existe", (MEMORY_DIR / "personality").exists(), 0.4),
    ], ["maturacao ainda e evidencia/contador, nao avaliacao profunda"])

    lab = run_comparison(lambda: 0.5, lambda: 0.7, threshold=0.1)
    scheduled_lab = schedule_experiment(
        {
            "hypothesis": "Runtime audit experiment proves lab can persist measured improvement candidates.",
            "baseline": "0.5",
            "variant": "0.7",
            "metric": "runtime_lab_delta",
            "threshold": 0.1,
            "rollback": "discard experiment result",
        }
    )
    add(9, "Lab proprio", 6.8, [
        ("lab comparison aceita melhoria medida", lab["accepted"], 0.7),
        ("lab dirs existem", all((ROOT / "lab" / name).exists() for name in ("experiments", "candidate_improvements", "reports")), 0.5),
        ("candidate improvements existem", any((ROOT / "lab" / "candidate_improvements").glob("*.json")), 0.5),
        ("experiencia runtime persistida com metrica", bool(scheduled_lab.get("path") and scheduled_lab.get("metric")), 0.4),
    ], extra={"scheduled_experiment": scheduled_lab})

    err = propose_regression_test("FileNotFoundError: missing config.json")
    add(10, "Registo de erros e terminal", 7.4, [
        ("error transcript dir existe", (LOGS_DIR / "transcripts" / "errors").exists(), 0.5),
        ("terminal transcript dir existe", (LOGS_DIR / "transcripts" / "tools").exists(), 0.4),
        ("erro vira proposta de teste", err["test_name"].startswith("test_prevent_error_"), 0.8),
        ("logs errors existem", (LOGS_DIR / "errors").exists(), 0.4),
    ])

    research_probe = run_runtime_research_probe()
    research_item = score_research_item({"title": "OpenAI agent memory benchmark", "url": "https://openai.com/research", "summary": "code benchmark for agents"})
    add(11, "Pesquisa diaria de tecnologia", 6.4, [
        ("research scoring funciona", research_item["source_quality"] >= 0.8, 0.6),
        ("daily research schedule no heartbeat", "daily_research_schedule" in str(heartbeat), 0.5),
        ("prompt jobs executaram sem login/codex erro", not any("Nao ha login Codex" in str(error) for error in cron_errors), 0.8),
        ("pesquisa web runtime buscou fonte externa", research_probe.get("ok", False), 0.5),
    ], ["jobs prompt dependem de login Codex guardado" if any("Nao ha login Codex" in str(error) for error in cron_errors) else ""], {"research_probe": research_probe})

    candidate = research_to_lab_candidate(research_item)
    add(12, "Pesquisa enviada para lab", 6.8, [
        ("research vira candidate com metrica", candidate.get("metric") == "capability_delta", 0.6),
        ("candidate tem rollback", bool(candidate.get("rollback")), 0.4),
        ("candidate tem expected_gain", candidate.get("expected_gain", 0) > 0, 0.5),
        ("probe real gerou candidate lab-ready", research_probe.get("lab_ready", False), 0.5),
    ], extra={"candidate": candidate, "research_probe_path": research_probe.get("path")})

    add(13, "Aprendizagem mundo/tecnologia separada", 7.0, [
        ("tecnologia classificada corretamente", validate_target_folder("OpenAI agent benchmark", "technology")["valid"], 0.5),
        ("world daily existe", (MEMORY_DIR / "world" / "daily").exists(), 0.4),
        ("technology daily existe", (MEMORY_DIR / "technology" / "daily").exists(), 0.4),
        ("personality daily existe", (MEMORY_DIR / "personality" / "daily").exists(), 0.4),
    ])

    arsi_candidate = {"files_changed": ["docs/arsi_runtime_probe.md"], "tests_required": ["runtime_audit"], "baseline_metric": 0.5, "new_metric": 0.65}
    arsi_result = run_arsi_cycle(arsi_candidate)
    add(14, "Melhoria autonoma do sistema", 6.5, [
        ("safe ARSI permitido", arsi_change_allowed(["docs/a.md"])["allowed"], 0.5),
        ("high risk bloqueado sem aprovacao", not arsi_change_allowed(["security/admin_gate.py"])["allowed"], 0.7),
        ("autonomy heartbeat criou/executou missao", bool((heartbeat.get("autonomy") or {}).get("executed_missions")), 0.6),
        ("ARSI safe cycle aplicou melhoria medida", arsi_result.get("applied", False), 0.5),
    ], ["melhoria medium/high continua a exigir humano"], {"arsi_result": arsi_result})

    add(15, "Controlo browser/UI humano", 4.9, [
        ("Eve web local responde", web_alive, 0.8),
        ("Playwright instalado/disponivel", deps["playwright"], 0.8),
        ("Playwright DOM smoke test real passou", playwright_smoke.get("ok", False), 0.7),
        ("UIA instalado/disponivel", deps["uiautomation"], 0.9),
        ("OCR dependency instalada", deps["pytesseract"], 0.3),
        ("Tesseract OCR executavel disponivel", bool(ocr.get("available")), 0.3),
        ("pyautogui instalado", deps["pyautogui"], 0.6),
        ("permissoes por app bloqueiam submit sensivel", not check_app_permission("chrome.exe", "click", selector={"name": "submit payment"})["allowed"], 0.5),
    ], ["Tesseract OCR executavel nao esta disponivel" if not ocr.get("available") else ""], {"dependencies": deps, "ocr": ocr, "playwright_smoke": playwright_smoke, "browser_snapshot": browser_dom_snapshot()})

    add(16, "ARSI - Autonomous Recursive Self Improvement", 6.4, [
        ("safe changes autonomas permitidas", arsi_change_allowed(["docs/a.md"])["allowed"], 0.5),
        ("high risk exige aprovacao", not arsi_change_allowed(["core/a.py"])["allowed"], 0.8),
        ("verified updates dir existe", (ROOT / "lab" / "candidate_improvements" / "verified_updates").exists(), 0.4),
        ("ARSI policy summary existe", arsi_policy_summary()["framework"] == "ARSI", 0.4),
        ("ARSI safe cycle executa com medicao", arsi_result.get("applied", False), 0.5),
    ], ["ARSI medium/high-risk continua controlado por aprovacao"], {"arsi_result": arsi_result})

    priority = score_mission(importance=1, urgency=0.5, risk=0.1, user_value=1, system_value=0.8, confidence=0.9)
    add(17, "Autonomia/proatividade sem input", 6.4, [
        ("daemon heartbeat existe", daemon_heartbeat.exists(), 0.6),
        ("autonomy executed missions no heartbeat", bool((heartbeat.get("autonomy") or {}).get("executed_missions")), 0.6),
        ("priority engine pontua missoes", priority["score"] > 0.7, 0.4),
        ("budget engine funciona", budget_allows("actions_per_hour", 0)["allowed"], 0.4),
        ("cron/prompt sem falhas", not cron_errors, 0.7),
    ], ["cron/prompt teve falhas recentes" if cron_errors else ""], {"cron_errors": cron_errors})

    average = round(sum(point["score"] for point in points) / len(points), 2)
    result = {
        "timestamp": _now(),
        "average_score": average,
        "web_alive": web_alive,
        "dependencies": deps,
        "cron_errors": cron_errors,
        "points": points,
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Runtime 17-Point Audit", "", f"Timestamp: {result['timestamp']}", f"Average score: {average}/10", ""]
    for point in points:
        lines.append(f"## {point['id']}. {point['title']}: {point['score']}/10")
        lines.append("- Evidence: " + (", ".join(point["evidence"]) or "none"))
        clean_limitations = [item for item in point["limitations"] if item]
        lines.append("- Limitations: " + (", ".join(clean_limitations) if clean_limitations else "none"))
        lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, ensure_ascii=False))
