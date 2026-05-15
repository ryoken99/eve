from __future__ import annotations

from runtime_validation_lib import check, finalize
from datetime import datetime

from core.personality_engine import update_preference_candidate
from core.paths import MEMORY_DIR
from personality.preference_lifecycle import update_preference


def main() -> dict:
    suffix = datetime.now().strftime("%Y%m%d%H%M%S")
    sandro = update_preference(f"Sandro runtime anime game dev {suffix}", "runtime evidence from Sandro", source="sandro", sentiment="positive")
    eve_topic = f"narrativa procedural auditavel runtime {suffix}"
    eve_1 = update_preference(eve_topic, "runtime test evidence 1", source="eve_research", sentiment="positive")
    eve_2 = update_preference(eve_topic, "runtime test evidence 2", source="experience", sentiment="positive")
    eve_3 = update_preference(eve_topic, "runtime test evidence 3", source="lab", sentiment="positive")
    conflict_topic = f"preferencia contraditoria runtime {suffix}"
    conflict_seed = update_preference(conflict_topic, "positive seed", source="eve_research", sentiment="positive")
    conflict = update_preference(conflict_topic, "runtime contradiction check", source="review", sentiment="negative")
    legacy = update_preference_candidate("computer use estruturado", "runtime reinforces DOM/UIA preference")
    path = MEMORY_DIR / "personality" / "preference_lifecycle.json"
    checks = [
        check("Sandro preference source is preserved", sandro["source"] == "sandro", sandro, critical=True),
        check("Eve preference matures to stable after repeated evidence", eve_3["status"] == "stable", eve_3, critical=True),
        check("Contradictory evidence creates conflict", conflict["status"] == "conflicted", conflict, critical=True),
        check("Candidate starts before maturity", eve_1["status"] == "candidate", eve_1),
        check("Second evidence reinforces before stable", eve_2["status"] == "reinforced", eve_2),
        check("Separate conflict topic began as candidate", conflict_seed["status"] == "candidate", conflict_seed),
        check("legacy preference candidate writes state", legacy["status"] in {"candidate", "reinforced", "stable"}, legacy),
        check("personality file exists", path.exists(), str(path), critical=True),
    ]
    return finalize("point_08_personality_runtime", "Point 08 Personality Runtime", "point_08_personality_runtime.md", checks)


if __name__ == "__main__":
    main()
