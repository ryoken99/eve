from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta

from continual_learning_common import CL_ROOT, append_jsonl, classify_risk, ensure_cl_dirs, excerpt, read_jsonl, read_text, stable_id


CANDIDATES_PATH = CL_ROOT / "improvement_candidates" / "self_improvement_candidates.jsonl"
APPROVALS_PATH = CL_ROOT / "approval_queue" / "pending_approvals.jsonl"


def default_date() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def existing_ids() -> set[str]:
    return {str(item.get("candidate_id")) for item in read_jsonl(CANDIDATES_PATH) if item.get("candidate_id")}


def candidate(date_key: str, problem: str, evidence: str, proposed_fix: str, target_files: list[str], test_plan: str, rollback_plan: str) -> dict:
    risk, approval = classify_risk(problem + " " + proposed_fix + " " + evidence, target_files)
    cid = stable_id("clcand", date_key, problem, evidence, proposed_fix, ",".join(target_files))
    return {
        "candidate_id": cid,
        "date": date_key,
        "problem": problem,
        "evidence": excerpt(evidence, 500),
        "proposed_fix": proposed_fix,
        "target_files": target_files,
        "risk_level": risk,
        "requires_approval": approval,
        "test_plan": test_plan,
        "rollback_plan": rollback_plan,
        "status": "proposed",
    }


def build_candidates(date_key: str, analysis: str, lessons: str) -> list[dict]:
    text = f"{analysis}\n{lessons}".lower()
    candidates: list[dict] = []
    if any(term in text for term in ("robot", "tom", "style/persona", "persona")):
        candidates.append(
            candidate(
                date_key,
                "Eve may sound too technical or robotic in personal replies.",
                "Daily analysis or lessons mention style/persona/tone.",
                "Review and refine memory/personality/style/eve_response_style.md with a small low-risk style adjustment.",
                ["memory/personality/style/eve_response_style.md"],
                "Preview terminal prompt and ask a personal identity/status question.",
                "Restore the previous style file from backup or revert the text block.",
            )
        )
    if any(term in text for term in ("erro", "error", "falha", "bug")):
        candidates.append(
            candidate(
                date_key,
                "A technical error or bug signal was detected.",
                "Daily errors or analysis mention errors/failures.",
                "Create a reproducible bug report and targeted test before changing runtime code.",
                ["tests/", "memory/continual_learning/daily_analysis/"],
                "Run the specific failing command or unit test after reproducing the bug.",
                "Do not change runtime until a patch exists; rollback is to discard the proposal.",
            )
        )
    if any(term in text for term in ("tool", "ferramenta")):
        candidates.append(
            candidate(
                date_key,
                "Tool usage may contain repeatable procedural lessons.",
                "Tool events were present in the daily analysis.",
                "Add or update procedural skill notes when a tool flow teaches a stable step.",
                ["memory/procedural/skills/"],
                "Run continual_learning_status.py and verify the skills registry stays valid JSON.",
                "Remove the proposed procedural note if it is inaccurate.",
            )
        )
    if any(term in text for term in ("memory conflict", "conflito", "conflict")):
        candidates.append(
            candidate(
                date_key,
                "Possible memory conflict detected.",
                "Daily candidates or analysis mention conflict/conflito.",
                "Create a memory conflict review candidate without overwriting stable memory.",
                ["memory/_processed/promotions/"],
                "Review conflict candidate manually; do not promote automatically.",
                "Mark candidate rejected if conflict was false positive.",
            )
        )
    if not candidates:
        candidates.append(
            candidate(
                date_key,
                "No actionable continual learning improvement detected.",
                "Daily analysis did not reveal strong repeated errors or feedback.",
                "Keep monitoring and avoid unnecessary changes.",
                [],
                "No test needed beyond status check.",
                "No change applied.",
            )
        )
    seen = existing_ids()
    return [item for item in candidates if item["candidate_id"] not in seen]


def main() -> int:
    parser = argparse.ArgumentParser(description="Propose safe self-improvement candidates from daily experience.")
    parser.add_argument("--date", default=default_date(), help="Date YYYY-MM-DD")
    args = parser.parse_args()
    ensure_cl_dirs()
    analysis_path = CL_ROOT / "daily_analysis" / f"{args.date}_experience_analysis.md"
    analysis = read_text(analysis_path)
    lessons = read_text(CL_ROOT / "lessons" / "lessons_learned.md")
    candidates = build_candidates(args.date, analysis, lessons)
    append_jsonl(CANDIDATES_PATH, candidates)
    approvals = [item for item in candidates if item.get("requires_approval")]
    append_jsonl(APPROVALS_PATH, approvals)
    print(json.dumps({"ok": True, "date": args.date, "candidates_added": len(candidates), "approvals_added": len(approvals), "path": str(CANDIDATES_PATH)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
