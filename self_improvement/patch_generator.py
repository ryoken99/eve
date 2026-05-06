from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.paths import LAB_DIR, ensure_project_dirs


def write_patch_proposal(name: str, summary: str, patch_text: str) -> Path:
    ensure_project_dirs()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.lower()).strip("_")
    path = LAB_DIR / "prototypes" / f"{safe}.patch.md"
    path.write_text(
        "\n".join(
            [
                f"# {name}",
                "",
                f"Created: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
                "",
                "## Summary",
                summary.strip(),
                "",
                "## Patch Proposal",
                "```diff",
                patch_text.rstrip(),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path
