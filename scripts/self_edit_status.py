from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.permission_manager import list_pending_permission_requests, permission_status_summary


SELF_EDIT_ROOT = ROOT / "memory" / "_processed" / "autonomy" / "self_edits"
METADATA_ROOT = SELF_EDIT_ROOT / "metadata"
POLICY_PATH = ROOT / "memory" / "_system" / "stage2_self_improvement_policy.yaml"


def main() -> int:
    edits = sorted(list(METADATA_ROOT.glob("selfedit_*.json")) + list(SELF_EDIT_ROOT.glob("selfedit_*.json")), key=lambda p: p.stat().st_mtime, reverse=True)[:10]
    rows = []
    for path in edits:
        try:
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        rows.append(
            {
                "change_id": payload.get("change_id"),
                "status": payload.get("status"),
                "risk": (payload.get("classification") or {}).get("risk"),
                "target_area": (payload.get("classification") or {}).get("target_area"),
                "rollback_available": payload.get("rollback_available", False),
            }
        )
    result = {
        "stage2_policy_exists": POLICY_PATH.exists(),
        "mode": "stage2_2_authorized_medium_high_self_editing",
        "codex_optional": True,
        "allowlist": ["memory/personality/style/eve_response_style.md", "memory/personality/preferences/"],
        "medium_high_allowed_with_one_shot_grant": True,
        "critical_requires_special_authorization": True,
        "permission_summary": permission_status_summary(),
        "latest_self_edits": rows,
        "pending_permission_requests": list_pending_permission_requests(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
