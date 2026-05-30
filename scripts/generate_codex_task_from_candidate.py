from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from continual_learning_common import CL_ROOT, ensure_cl_dirs, read_jsonl


CANDIDATES_PATH = CL_ROOT / "improvement_candidates" / "self_improvement_candidates.jsonl"
TASK_QUEUE_PATH = CL_ROOT / "codex_tasks" / "codex_task_queue.jsonl"


def now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load_candidate(candidate_id: str) -> dict | None:
    for item in read_jsonl(CANDIDATES_PATH):
        if item.get("candidate_id") == candidate_id:
            return item
    return None


def target_codex(candidate: dict) -> str:
    files = " ".join(candidate.get("target_files") or []).lower()
    if any(term in files for term in ("memory/", "telegram", "webui", "app/", "tools/", "runtime")):
        return "Codex 2"
    return "Codex 1"


def write_task(candidate: dict) -> Path:
    ensure_cl_dirs()
    codex = target_codex(candidate)
    date_key = now_date()
    cid = candidate["candidate_id"]
    output = CL_ROOT / "codex_tasks" / f"{date_key}_{cid}_codex_task.md"
    lines = [
        f"# Codex Task - {cid}",
        "",
        f"Target: {codex}",
        "",
        "## Objectivo",
        candidate.get("proposed_fix", ""),
        "",
        "## Problema",
        candidate.get("problem", ""),
        "",
        "## Evidencia",
        candidate.get("evidence", ""),
        "",
        "## Ficheiros alvo",
    ]
    lines.extend([f"- {item}" for item in candidate.get("target_files") or ["No direct file target; inspect first."]])
    lines.extend(
        [
            "",
            "## Restricoes",
            "- Trabalhar em E:\\eve.",
            "- Nao apagar memoria ou transcricoes.",
            "- Nao mexer em secrets/tokens.",
            "- Nao fazer git add, commit ou push sem ordem explicita.",
            "- Nao enviar dados privados para GitHub.",
            "- Manter Eve como nome canonico.",
            "",
            "## Passos",
            "1. Auditar os ficheiros alvo.",
            "2. Confirmar risco e escopo.",
            "3. Implementar a menor alteracao segura.",
            "4. Correr testes.",
            "5. Reportar resultados a Sandro.",
            "",
            "## Testes",
            candidate.get("test_plan", ""),
            "",
            "## Rollback",
            candidate.get("rollback_plan", ""),
            "",
            "## Git Rules",
            "- Nao usar git add .",
            "- Nao commitar memory/transcripts/vector/state/logs/secrets.",
            "- Mostrar git status antes de qualquer commit futuro.",
            "",
            "## Reportar ao Sandro",
            "- O que foi alterado.",
            "- Testes executados.",
            "- Riscos restantes.",
            "- Se houve ou nao alteracao real.",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with TASK_QUEUE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"created_at": datetime.now().astimezone().isoformat(timespec="seconds"), "candidate_id": cid, "target": codex, "task_path": str(output), "status": "created"}, ensure_ascii=False) + "\n")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Codex-ready task from a continual learning candidate.")
    parser.add_argument("--candidate-id", required=True)
    args = parser.parse_args()
    candidate = load_candidate(args.candidate_id)
    if not candidate:
        print(json.dumps({"ok": False, "error": "candidate not found", "candidate_id": args.candidate_id}, ensure_ascii=False, indent=2))
        return 1
    output = write_task(candidate)
    print(json.dumps({"ok": True, "candidate_id": args.candidate_id, "path": str(output), "target": target_codex(candidate)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
