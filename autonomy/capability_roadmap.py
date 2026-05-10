from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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


def _exists(relative: str) -> bool:
    path = (EVE_ROOT / relative).resolve()
    return path.exists()


def _score_point(point: dict[str, Any]) -> dict[str, Any]:
    paths = point.get("paths") or []
    existing = [path for path in paths if _exists(str(path))]
    ratio = len(existing) / max(1, len(paths))
    if ratio >= 1:
        status = "implemented_base"
    elif ratio > 0:
        status = "partial"
    else:
        status = "missing"
    maturity = {
        "implemented_base": "needs_autonomous_habit",
        "partial": "needs_core_work",
        "missing": "needs_foundation",
    }[status]
    return {
        "id": point["id"],
        "title": point["title"],
        "status": status,
        "maturity": maturity,
        "desired": point["desired"],
        "evidence": existing,
        "missing_paths": [path for path in paths if path not in existing],
        "score": round(ratio, 2),
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
        lines.append(f"- Objetivo: {point['desired']}")
        lines.append(f"- Evidencia: {', '.join(point['evidence']) or 'nenhuma'}")
        lines.append(f"- Falta: {', '.join(point['missing_paths']) or 'nenhum caminho base'}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
