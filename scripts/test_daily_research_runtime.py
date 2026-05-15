from __future__ import annotations

from runtime_validation_lib import check, finalize

from core.paths import MEMORY_DIR
from research.technology_watcher import classify_research_item, run_technology_watch, technology_source_plan


def main() -> dict:
    plan = technology_source_plan()
    path = run_technology_watch(limit_per_source=1)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    classified = classify_research_item("Computer use agent benchmark", "browser automation memory evaluation")
    checks = [
        check("technology source plan includes frontier labs", "frontier_labs" in plan.get("groups", {}), plan, critical=True),
        check("technology watch writes memory file", path.exists(), str(path), critical=True),
        check("technology watch records source names", "openai_blog" in text or "arxiv_ai" in text, text[:1000], critical=True),
        check("research classifier marks agent benchmark useful", classified["useful"] and classified["category"] in {"agents", "memory", "self_improvement"}, classified, critical=True),
        check("technology memory directory exists", (MEMORY_DIR / "technology").exists(), str(MEMORY_DIR / "technology")),
    ]
    return finalize("point_11_research_runtime", "Point 11 Daily Technology Research Runtime", "point_11_research_runtime.md", checks)


if __name__ == "__main__":
    main()
