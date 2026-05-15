from __future__ import annotations

from runtime_validation_lib import check, finalize

from core.paths import MEMORY_DIR
from dream.dream_cycle import run_dream_cycle


def main() -> dict:
    result = run_dream_cycle()
    report = result.get("memory_report") or result.get("dream_report")
    queue = result.get("queue")
    checks = [
        check("dream cycle returns report path", bool(report), result, critical=True),
        check("dream report exists", bool(report) and __import__("pathlib").Path(report).exists(), report, critical=True),
        check("dream queue candidate exists", bool(queue) and __import__("pathlib").Path(queue).exists(), queue, critical=True),
        check("memory decisions generated", bool(result.get("memory_decisions")), result.get("memory_decisions"), critical=True),
        check("dream report mirrored under memory/dream_reports", any((MEMORY_DIR / "dream_reports").glob("dream_*.md")), str(MEMORY_DIR / "dream_reports")),
    ]
    return finalize("point_06_dream_runtime", "Point 06 Dream Runtime", "point_06_dream_runtime.md", checks, result)


if __name__ == "__main__":
    main()
