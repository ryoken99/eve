from __future__ import annotations

import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from computer.ui_action_log import log_ui_action
from core.paths import LOGS_DIR, ensure_project_dirs
from tools.browser_human import open_url


def create_gmail_draft(to: str, subject: str, body: str, *, open_browser: bool = True) -> dict:
    ensure_project_dirs()
    drafts_dir = LOGS_DIR / "email_drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    draft_path = drafts_dir / f"draft_{timestamp}.md"
    draft_path.write_text(
        "\n".join(
            [
                f"To: {to}",
                f"Subject: {subject}",
                "",
                body,
                "",
                "Status: draft_only_not_sent",
            ]
        ),
        encoding="utf-8",
    )
    result = {"draft": str(draft_path), "to": to, "subject": subject, "opened_browser": False}
    if open_browser:
        params = urllib.parse.urlencode({"to": to, "su": subject, "body": body})
        url = f"https://mail.google.com/mail/?view=cm&fs=1&{params}"
        browser_result = open_url(url)
        result["opened_browser"] = True
        result["browser"] = browser_result
    log_ui_action("email_draft_created", result)
    return result
