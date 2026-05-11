from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from autonomy.cron_manager import add_cron_job, list_cron_jobs
from core.paths import EVE_ROOT, LAB_DIR, LOGS_DIR, MEMORY_DIR, STATE_DIR, ensure_project_dirs


CAPABILITY_POINTS: list[dict[str, Any]] = [
    {"id": 1, "title": "Permissoes elevadas/admin", "paths": ["tools/admin_executor.py", "security/admin_gate.py"], "desired": "admin temporario auditado"},
    {"id": 2, "title": "Diario completo das conversas", "paths": ["memory/diary_manager.py", "logs/transcripts/chat"], "desired": "todas as mensagens em diario/transcript"},
    {"id": 3, "title": "Consolidacao diaria varias vezes por dia", "paths": ["dream/diary_consolidator.py", "autonomy/daemon.py"], "desired": "consolidacao periodica automatica"},
    {"id": 4, "title": "Memoria curta/media/longa", "paths": ["memory/short_term", "memory/medium_term", "memory/long_term"], "desired": "camadas separadas e consultaveis"},
    {"id": 5, "title": "Memoria semantica/vectorial", "paths": ["memory/semantic_vector", "memory/vector_provider.py"], "desired": "prefetch semantico em contexto"},
    {"id": 6, "title": "Sistema de sonhos", "paths": ["dream/dream_cycle.py", "dream/memory_reorganizer.py"], "desired": "sonhos autonomos e curadoria de memoria"},
    {"id": 7, "title": "Awareness temporal/situacional/espacial", "paths": ["core/awareness_engine.py", "computer/active_window.py", "computer/vision.py"], "desired": "percepcao periodica do ambiente"},
    {"id": 8, "title": "Vontade/gostos/personalidade evolutiva", "paths": ["core/personality_engine.py", "memory/personality"], "desired": "preferencias proprias evolutivas"},
    {"id": 9, "title": "Lab proprio", "paths": ["lab", "lab/lab_manager.py"], "desired": "experiencias por curiosidade propria"},
    {"id": 10, "title": "Registo de erros e terminal", "paths": ["memory/errors", "logs/transcripts/errors", "logs/transcripts/tools"], "desired": "erros e terminal sempre analisaveis"},
    {"id": 11, "title": "Pesquisa diaria de tecnologia", "paths": ["research/technology_watcher.py", "tools/web_research.py"], "desired": "watchers diarios de labs/open source"},
    {"id": 12, "title": "Pesquisa enviada para lab", "paths": ["memory/technology/research_candidates.md", "lab/candidate_improvements"], "desired": "research vira candidato de experiencia"},
    {"id": 13, "title": "Aprendizagem do mundo e tecnologia separada", "paths": ["memory/world/world_learning.md", "memory/technology/technology_learning.md"], "desired": "ficheiros separados antes do lab"},
    {"id": 14, "title": "Melhoria autonoma do sistema", "paths": ["autonomy/autonomy_director.py", "self_improvement/verified_self_update.py"], "desired": "melhorias propostas e testadas sem pedido manual"},
    {"id": 15, "title": "Controlo browser/UI humano", "paths": ["tools/browser_human.py", "computer/mouse_control.py", "computer/keyboard_control.py", "computer/screen_capture.py"], "desired": "browser/teclado/rato/OCR com verificacao"},
    {"id": 16, "title": "Recursive self-improvement", "paths": ["self_improvement/recursive_self_improvement.py", "self_improvement/verified_self_update.py"], "desired": "RSI controlado com sandbox, testes e rollback"},
    {"id": 17, "title": "Autonomia/proatividade sem input", "paths": ["autonomy/daemon.py", "autonomy/proactive_decider.py", "autonomy/autonomous_executor.py"], "desired": "acoes autonomas, mensagens e melhorias com o tempo"},
]

TARGET_CAPABILITY_SCORE = 8.3


EIGHT_THREE_CRITERIA: dict[int, list[str]] = {
    1: ["admin gate exists", "admin actions are audited", "elevated launch path is documented/tested"],
    2: ["chat transcript exists", "tool/action transcript exists", "web/console/autonomous messages are captured"],
    3: ["diary consolidation exists", "recurring schedule exists", "consolidation outputs have evidence"],
    4: ["short memory exists", "medium memory exists", "long memory exists", "promotion rules exist"],
    5: ["semantic index exists", "prefetch enters context", "recent memories can be rebuilt/indexed"],
    6: ["dream cycle exists", "dream reports are written", "memory layer decisions are recorded"],
    7: ["time/system awareness exists", "screen/window awareness exists", "tools verify visible state before success claims"],
    8: ["preference memory exists", "daily interest research exists", "candidate preferences can mature or be rejected"],
    9: ["lab folders exist", "experiments can be created", "self-chosen candidates are tracked"],
    10: ["terminal logs exist", "error memory exists", "errors can become lessons/candidates"],
    11: ["technology watcher exists", "web research exists", "daily research pipeline covers labs/open source/papers"],
    12: ["research candidates exist", "lab candidate path exists", "research-to-lab rule exists"],
    13: ["world daily file exists", "technology daily file exists", "personality daily file exists"],
    14: ["autonomy director exists", "verified self update exists", "improvement candidates are tested before core changes"],
    15: ["browser control exists", "keyboard/mouse control exists", "screenshot/OCR verification exists"],
    16: ["RSI policy/module exists", "sandbox testing exists", "rollback/backup exists"],
    17: ["daemon exists", "cron/jobs exist", "autonomous mission execution exists", "proactive messages are possible"],
}


def _exists(relative: str) -> bool:
    path = (EVE_ROOT / relative).resolve()
    return path.exists()


def _count_files(relative: str, pattern: str = "*") -> int:
    path = (EVE_ROOT / relative).resolve()
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    return sum(1 for item in path.rglob(pattern) if item.is_file())


def _habit_score(point_id: int) -> tuple[float, list[str]]:
    evidence: list[str] = []
    checks = {
        1: [("logs/admin_actions", 1), ("backups/files", 1)],
        2: [("logs/transcripts/chat", 1), ("memory/diary", 1)],
        3: [("memory/medium_term", 1), ("memory/dream_reports", 1)],
        4: [("memory/short_term", 1), ("memory/medium_term", 1), ("memory/long_term", 1)],
        5: [("memory/semantic_vector", 1)],
        6: [("memory/dream_reports", 1)],
        7: [("logs/ui_actions", 1), ("logs/browser", 1)],
        8: [("memory/personality", 1), ("memory/medium_term/autonomous_capability_improvements.md", 1)],
        9: [("lab/candidate_improvements", 1), ("lab/reports", 1)],
        10: [("logs/transcripts/errors", 1), ("memory/errors", 1)],
        11: [("memory/technology", 1), ("logs/browser", 1)],
        12: [("memory/technology/research_candidates.md", 1), ("lab/candidate_improvements", 1)],
        13: [("memory/world/world_learning.md", 1), ("memory/technology/technology_learning.md", 1)],
        14: [("logs/autonomy", 1), ("lab/candidate_improvements", 1)],
        15: [("logs/ui_actions", 1), ("logs/browser", 1)],
        16: [("backups/tmp", 1), ("lab/candidate_improvements/verified_updates", 1)],
        17: [("state/daemon_heartbeat.json", 1), ("state/missions", 1), ("logs/autonomy", 1)],
    }
    selected = checks.get(point_id, [])
    passed = 0
    for relative, minimum in selected:
        count = _count_files(relative)
        if count >= minimum:
            passed += 1
            evidence.append(f"{relative} ({count})")
    return (passed / max(1, len(selected))), evidence


def _improvement_score(point_id: int) -> tuple[float, list[str]]:
    evidence: list[str] = []
    candidate_count = _count_files("lab/candidate_improvements", "*.json")
    report_count = _count_files("memory/medium_term", "*capability*.md")
    if candidate_count:
        evidence.append(f"lab/candidate_improvements ({candidate_count})")
    if report_count:
        evidence.append(f"memory/medium_term capability reports ({report_count})")
    score = 0.0
    if candidate_count:
        score += 0.5
    if report_count:
        score += 0.25
    if (STATE_DIR / "capability_roadmap_state.json").exists():
        score += 0.25
        evidence.append("state/capability_roadmap_state.json")
    return min(1.0, score), evidence


def _score_point(point: dict[str, Any]) -> dict[str, Any]:
    paths = point.get("paths") or []
    existing = [path for path in paths if _exists(str(path))]
    base_score = len(existing) / max(1, len(paths))
    habit_score, habit_evidence = _habit_score(int(point["id"]))
    improvement_score, improvement_evidence = _improvement_score(int(point["id"]))
    closeness = round(base_score * 0.45 + habit_score * 0.35 + improvement_score * 0.20, 2)
    score_10 = round(closeness * 10, 1)
    improvement_headroom = round(1.0 - closeness, 2)
    criteria = EIGHT_THREE_CRITERIA.get(int(point["id"]), [])
    goal_gaps = []
    if base_score < 1.0:
        goal_gaps.append("base paths incomplete")
    if habit_score < 0.75:
        goal_gaps.append("autonomous habit/evidence too weak")
    if improvement_score < 0.5:
        goal_gaps.append("improvement/lab evidence too weak")
    if score_10 < TARGET_CAPABILITY_SCORE:
        goal_gaps.append(f"score below {TARGET_CAPABILITY_SCORE}/10")
    if base_score >= 1:
        status = "implemented_base"
    elif base_score > 0:
        status = "partial"
    else:
        status = "missing"
    if status == "missing":
        maturity = "needs_foundation"
    elif status == "partial":
        maturity = "needs_core_work"
    elif closeness >= 0.85:
        maturity = "improve_quality"
    elif habit_score >= 0.5:
        maturity = "needs_depth"
    else:
        maturity = "needs_autonomous_habit"
    return {
        "id": point["id"],
        "title": point["title"],
        "status": status,
        "maturity": maturity,
        "desired": point["desired"],
        "evidence": existing,
        "habit_evidence": habit_evidence,
        "improvement_evidence": improvement_evidence,
        "missing_paths": [path for path in paths if path not in existing],
        "base_score": round(base_score, 2),
        "habit_score": round(habit_score, 2),
        "improvement_score": round(improvement_score, 2),
        "closeness": closeness,
        "score_10": score_10,
        "target_score": TARGET_CAPABILITY_SCORE,
        "meets_goal": score_10 >= TARGET_CAPABILITY_SCORE,
        "goal_criteria": criteria,
        "goal_gaps": goal_gaps,
        "improvement_headroom": improvement_headroom,
        "score": closeness,
    }


def capability_audit() -> dict[str, Any]:
    ensure_project_dirs()
    points = [_score_point(point) for point in CAPABILITY_POINTS]
    summary = {
        "total": len(points),
        "implemented_base": sum(1 for point in points if point["status"] == "implemented_base"),
        "partial": sum(1 for point in points if point["status"] == "partial"),
        "missing": sum(1 for point in points if point["status"] == "missing"),
        "needs_autonomous_habit": sum(1 for point in points if point["maturity"] == "needs_autonomous_habit"),
        "average_closeness": round(sum(point["closeness"] for point in points) / max(1, len(points)), 2),
        "average_score_10": round(sum(point["score_10"] for point in points) / max(1, len(points)), 1),
        "target_score": TARGET_CAPABILITY_SCORE,
        "points_meeting_target": sum(1 for point in points if point["meets_goal"]),
        "points_below_target": sum(1 for point in points if not point["meets_goal"]),
        "all_meet_target": all(point["meets_goal"] for point in points),
    }
    weakest = sorted(points, key=lambda item: (item["score"], item["id"]))[:5]
    return {"summary": summary, "points": points, "weakest": weakest}


def capability_impulses(limit: int = 3) -> list[dict[str, Any]]:
    return _capability_impulses_from_points(capability_audit()["weakest"], limit=limit)


def rotating_capability_impulses(limit: int = 3) -> list[dict[str, Any]]:
    audit = capability_audit()
    points = audit["points"]
    state_path = STATE_DIR / "capability_roadmap_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    except Exception:
        state = {}
    last_id = int(state.get("last_focus_id") or 0)
    ordered = sorted(points, key=lambda item: item["id"])
    start_index = 0
    for index, point in enumerate(ordered):
        if point["id"] > last_id:
            start_index = index
            break
    else:
        start_index = 0
    rotated = ordered[start_index:] + ordered[:start_index]
    selected = rotated[: max(1, int(limit))]
    if selected:
        state_path.write_text(json.dumps({"last_focus_id": selected[-1]["id"]}, indent=2), encoding="utf-8")
    return _capability_impulses_from_points(selected, limit=limit)


def _capability_impulses_from_points(points: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    impulses = []
    for point in points[: max(1, int(limit))]:
        impulses.append(
            {
                "kind": "capability_improvement",
                "title": f"Melhorar ponto {point['id']}: {point['title']}",
                "reason": f"Roadmap interno marcou maturidade {point['maturity']} para: {point['desired']}.",
                "risk": "low",
                "plan": [
                    "Ler evidencias existentes do ponto",
                    "Criar nota de lacuna e proposta de melhoria",
                    "Criar candidato no lab sem alterar core automaticamente",
                ],
                "permissions": ["read_memory", "write_memory"],
                "capability_point": point,
            }
        )
    return impulses


def write_capability_audit() -> Path:
    audit = capability_audit()
    path = MEMORY_DIR / "medium_term" / "eve_capability_roadmap.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Eve Capability Roadmap",
        "",
        f"Resumo: {audit['summary']}",
        "",
    ]
    for point in audit["points"]:
        lines.append(f"## {point['id']}. {point['title']}")
        lines.append(f"- Estado: {point['status']}")
        lines.append(f"- Maturidade: {point['maturity']}")
        lines.append(f"- Proximidade: {point['closeness']} | Margem de melhoria: {point['improvement_headroom']}")
        lines.append(f"- Score 0-10: {point['score_10']} / alvo {point['target_score']} | Cumpre alvo: {point['meets_goal']}")
        lines.append(f"- Scores: base={point['base_score']} habito={point['habit_score']} melhoria={point['improvement_score']}")
        lines.append(f"- Objetivo: {point['desired']}")
        lines.append(f"- Criterios 8.3+: {', '.join(point['goal_criteria']) or 'nao definido'}")
        lines.append(f"- Lacunas para alvo: {', '.join(point['goal_gaps']) or 'nenhuma'}")
        lines.append(f"- Evidencia: {', '.join(point['evidence']) or 'nenhuma'}")
        lines.append(f"- Habito autonomo: {', '.join(point['habit_evidence']) or 'nenhum'}")
        lines.append(f"- Evidencia de melhoria: {', '.join(point['improvement_evidence']) or 'nenhuma'}")
        lines.append(f"- Falta: {', '.join(point['missing_paths']) or 'nenhum caminho base'}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def append_capability_review_history() -> Path:
    audit = capability_audit()
    path = LOGS_DIR / "autonomy" / "capability_reviews.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "summary": audit["summary"],
        "weakest": audit["weakest"],
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def ensure_capability_review_schedule(*, schedule: str = "6h") -> dict[str, Any]:
    command = "Set-Location D:\\Eve; python scripts\\capability_review.py"
    existing = [
        job
        for job in list_cron_jobs()
        if job.get("name") == "Eve Capability Roadmap Review"
    ]
    if existing:
        return {"status": "exists", "job": existing[0]}
    job = add_cron_job("Eve Capability Roadmap Review", schedule, command, enabled=True)
    return {"status": "created", "job": job}
