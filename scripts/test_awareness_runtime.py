from __future__ import annotations

import json

from runtime_validation_lib import check, finalize, powershell

from computer.environment_state import capture_environment_state
from core.awareness_engine import collect_awareness
from core.paths import STATE_DIR


def main() -> dict:
    awareness = collect_awareness()
    state_before = capture_environment_state(include_screen=False, include_uia=True, include_browser=True)
    chrome = powershell("Start-Process chrome.exe -ArgumentList 'about:blank'; Start-Sleep -Seconds 2", timeout=20)
    state_after_chrome = capture_environment_state(include_screen=False, include_uia=True, include_browser=True)
    ps = powershell("Start-Process powershell.exe -ArgumentList '-NoExit','-Command','Write-Host EveRuntimeAwareness'; Start-Sleep -Seconds 1", timeout=20)
    state_after_ps = capture_environment_state(include_screen=False, include_uia=True, include_browser=True)
    world_state = STATE_DIR / "current_world_state.json"
    world_state.write_text(json.dumps({"awareness": awareness, "state": state_after_ps}, indent=2, ensure_ascii=False), encoding="utf-8")
    checks = [
        check("timezone captured", awareness.get("timezone") == "Europe/Lisbon", awareness.get("timezone"), critical=True),
        check("active window captured", "active_window" in awareness.get("desktop", {}), awareness.get("desktop"), critical=True),
        check("system status captured", awareness.get("system", {}).get("os") == "Windows", awareness.get("system"), critical=True),
        check("environment state captures UIA/browser fields", "uia" in state_before and "browser" in state_before, state_before, critical=True),
        check("Chrome launch command executed", chrome["returncode"] == 0, chrome),
        check("PowerShell launch command executed", ps["returncode"] == 0, ps),
        check("current_world_state.json written", world_state.exists(), str(world_state), critical=True),
        check("post-launch awareness has active window string", bool(state_after_chrome.get("active_window") or state_after_ps.get("active_window")), {"chrome": state_after_chrome.get("active_window"), "ps": state_after_ps.get("active_window")}),
    ]
    return finalize("point_07_awareness_runtime", "Point 07 Awareness Runtime", "point_07_awareness_runtime.md", checks)


if __name__ == "__main__":
    main()
