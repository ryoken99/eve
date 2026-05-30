from __future__ import annotations

import json

from continual_learning_common import CL_ROOT, MEMORY_ROOT, read_jsonl, read_text


def count_lessons(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith("## ") and "lesson_" in line)


def main() -> int:
    policy_path = CL_ROOT / "continual_learning_policy.yaml"
    lessons_text = read_text(CL_ROOT / "lessons" / "lessons_learned.md")
    candidates = read_jsonl(CL_ROOT / "improvement_candidates" / "self_improvement_candidates.jsonl")
    approvals = read_jsonl(CL_ROOT / "approval_queue" / "pending_approvals.jsonl")
    tasks = read_jsonl(CL_ROOT / "codex_tasks" / "codex_task_queue.jsonl")
    registry_path = MEMORY_ROOT / "procedural" / "skills" / "skills_registry.json"
    try:
        registry = json.loads(read_text(registry_path) or "{}")
    except json.JSONDecodeError:
        registry = {}
    skills = registry.get("skills") or []
    payload = {
        "ok": True,
        "policy_active": "enabled: true" in read_text(policy_path),
        "lessons_active": count_lessons(lessons_text),
        "candidates_proposed": sum(1 for item in candidates if item.get("status") == "proposed"),
        "candidates_approved": sum(1 for item in candidates if item.get("status") == "approved"),
        "pending_approvals": len([item for item in approvals if item.get("status") == "proposed"]),
        "codex_tasks_created": len(tasks),
        "latest_lessons": [line[3:] for line in lessons_text.splitlines() if line.startswith("## ")][-5:],
        "latest_candidates": [
            {"candidate_id": item.get("candidate_id"), "problem": item.get("problem"), "risk": item.get("risk_level")}
            for item in candidates[-5:]
        ],
        "skills_known": len(skills),
        "skills_tested": sum(1 for item in skills if item.get("status") == "tested"),
        "skills_needing_review": sum(1 for item in skills if item.get("status") == "needs_review"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
