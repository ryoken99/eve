from __future__ import annotations

from runtime_validation_lib import check, finalize

from lab.lab_manager import create_candidate
from memory.errors.error_memory import record_error
from self_improvement.improvement_planner import plan_autonomous_system_improvements, propose_improvement
from self_improvement.verified_self_update import verified_core_update


def main() -> dict:
    err = record_error("runtime", "autonomous improvement", "runtime_gap", "capability gap fake", lesson="turn gap into test", resolved=False)
    plan = plan_autonomous_system_improvements(target_score=8.6, max_items=3)
    proposal = propose_improvement("runtime_validation", "fake gap", "add runtime test", risk="low")
    lab_candidate = create_candidate("runtime_autonomous_improvement", "gap becomes lab candidate", metric="capability_delta")
    update = verified_core_update("workspace/arsi_safe_runtime.py", "VALUE = 42\n", tests=["py_compile_candidate"], approved=True)
    checks = [
        check("error recorded with lesson", bool(err.get("lesson")), err, critical=True),
        check("improvement planner returns items", bool(plan.get("items") or plan.get("planned")), plan, critical=True),
        check("improvement proposal file exists", proposal.exists(), str(proposal), critical=True),
        check("lab candidate created", lab_candidate.exists(), str(lab_candidate), critical=True),
        check("verified self update applies safe workspace file", update.get("applied"), update, critical=True),
    ]
    return finalize("point_14_autonomous_improvement_runtime", "Point 14 Autonomous Improvement Runtime", "point_14_autonomous_improvement_runtime.md", checks)


if __name__ == "__main__":
    main()
