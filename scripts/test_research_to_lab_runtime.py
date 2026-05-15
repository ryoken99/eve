from __future__ import annotations

from pathlib import Path

from runtime_validation_lib import check, finalize

from research.research_notes import decide_research_for_lab


def main() -> dict:
    test_lab = decide_research_for_lab("Agent memory benchmark", "tool browser automation and memory evaluation", confidence=0.9)
    watch = decide_research_for_lab("RAG browser agent", "agent memory tool", confidence=0.65)
    ignore = decide_research_for_lab("Garden furniture", "chairs and tables", confidence=0.9)
    review = decide_research_for_lab("Security rollback method", "rollback and security", confidence=0.4)
    checks = [
        check("high confidence useful research goes to lab", test_lab["decision"] == "test_in_lab" and bool(test_lab["candidate"]), test_lab, critical=True),
        check("medium confidence useful research goes to watch", watch["decision"] == "watch", watch, critical=True),
        check("irrelevant research is ignored", ignore["decision"] == "ignore", ignore, critical=True),
        check("security rollback is apply_after_review", review["decision"] == "apply_after_review", review, critical=True),
        check("lab candidate file exists for test_in_lab", bool(test_lab["candidate"]) and Path(test_lab["candidate"]).exists(), test_lab["candidate"], critical=True),
    ]
    return finalize("point_12_research_to_lab_runtime", "Point 12 Research To Lab Runtime", "point_12_research_to_lab_runtime.md", checks)


if __name__ == "__main__":
    main()
