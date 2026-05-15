from __future__ import annotations

import json

from runtime_validation_lib import check, finalize

from lab.lab_manager import create_candidate, record_candidate_result


def main() -> dict:
    accepted_path = create_candidate("runtime_lab_accept", "variant improves runtime metric", metric="runtime_metric")
    payload = json.loads(accepted_path.read_text(encoding="utf-8"))
    payload["status"] = "planned"
    accepted_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    accepted = record_candidate_result("runtime_lab_accept", metric_value=0.9, threshold=0.8, notes="runtime accept")
    rejected_path = create_candidate("runtime_lab_reject", "variant worsens runtime metric", metric="runtime_metric")
    rejected = record_candidate_result("runtime_lab_reject", metric_value=-0.1, threshold=0.8, notes="runtime reject")
    checks = [
        check("candidate file created", accepted_path.exists(), str(accepted_path), critical=True),
        check("candidate can be moved to planned", json.loads(accepted_path.read_text(encoding="utf-8")).get("results") is not None, str(accepted_path), critical=True),
        check("accepted decision recorded", accepted["result"]["decision"] == "accept", accepted, critical=True),
        check("rejected decision recorded", rejected["result"]["decision"] == "reject", rejected, critical=True),
        check("rejected candidate file exists", rejected_path.exists(), str(rejected_path)),
    ]
    return finalize("point_09_lab_runtime", "Point 09 Lab Runtime", "point_09_lab_runtime.md", checks)


if __name__ == "__main__":
    main()
