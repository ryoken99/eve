from __future__ import annotations

import subprocess

from security.audit_log import log_event


def notify(title: str, message: str) -> dict:
    ps = (
        "[reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null; "
        "$n = New-Object System.Windows.Forms.NotifyIcon; "
        "$n.Icon = [System.Drawing.SystemIcons]::Information; "
        "$n.BalloonTipTitle = " + repr(title) + "; "
        "$n.BalloonTipText = " + repr(message) + "; "
        "$n.Visible = $true; "
        "$n.ShowBalloonTip(5000); Start-Sleep -Seconds 1; $n.Dispose()"
    )
    completed = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=20)
    result = {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    log_event("notification_sent", {"title": title, "message": message, **result})
    return result
