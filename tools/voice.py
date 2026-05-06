from __future__ import annotations

import subprocess

from security.audit_log import log_event


def speak(text: str) -> dict:
    command = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Speak(" + repr(text) + ")"
    )
    completed = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True, timeout=60)
    result = {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    log_event("voice_speak", {"chars": len(text), **result})
    return result
