from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from tools.windows_scheduler import create_once_task
from tools.x_scheduler import target_datetime_for_time


def desktop_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"


def safe_desktop_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\r\n]+', "_", name.strip()).strip(" .")
    return cleaned or "eve_item"


def parse_desktop_file_request(prompt: str) -> dict | None:
    lowered = prompt.lower()
    if "ficheiro" not in lowered or "ambiente de trabalho" not in lowered:
        return None
    match = re.search(r"ficheiro\s+no\s+ambiente\s+de\s+trabalho\s+chamad[oa]\s+([^,.;]+)", prompt, re.IGNORECASE)
    if not match:
        match = re.search(r"ficheiro\s+chamad[oa]\s+([^,.;]+).*ambiente\s+de\s+trabalho", prompt, re.IGNORECASE)
    if not match:
        return {"status": "needs_confirmation", "reason": "missing_file_name"}
    return {"name": safe_desktop_name(match.group(1))}


def parse_desktop_folder_request(prompt: str) -> dict | None:
    lowered = prompt.lower()
    if "pasta" not in lowered or "ambiente de trabalho" not in lowered:
        return None
    if any(word in lowered for word in ("agenda", "agendar", "programa", "programar", "schedule")):
        return None
    match = re.search(r"pasta\s+no\s+ambiente\s+de\s+trabalho\s+chamad[ao]\s+([^,.;]+)", prompt, re.IGNORECASE)
    if not match:
        match = re.search(r"pasta\s+chamad[ao]\s+([^,.;]+).*ambiente\s+de\s+trabalho", prompt, re.IGNORECASE)
    if not match:
        return {"status": "needs_confirmation", "reason": "missing_folder_name"}
    return {"name": safe_desktop_name(match.group(1))}


def parse_desktop_folder_schedule_request(prompt: str) -> dict | None:
    lowered = prompt.lower()
    if not any(word in lowered for word in ("agenda", "agendar", "programa", "programar", "schedule")):
        return None
    if "pasta" not in lowered or "ambiente de trabalho" not in lowered:
        return None
    time_match = re.search(r"\b(?:as|às|para as|para|for)\s*([01]?\d|2[0-3]):([0-5]\d)\b", lowered)
    if not time_match:
        time_match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", lowered)
    if not time_match:
        return {"status": "needs_confirmation", "reason": "missing_time"}
    time_hhmm = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
    name_match = re.search(r"pasta\s+(?:no\s+ambiente\s+de\s+trabalho\s+)?chamad[ao]\s+([^,.;]+)", prompt, re.IGNORECASE)
    name = safe_desktop_name(name_match.group(1)) if name_match else f"pasta_agendada_eve_{time_hhmm.replace(':', '')}"
    return {"time": time_hhmm, "name": name}


def create_desktop_file(name: str) -> dict:
    path = desktop_dir() / safe_desktop_name(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return {"status": "created", "path": str(path)}


def create_desktop_folder(name: str) -> dict:
    path = desktop_dir() / safe_desktop_name(name)
    path.mkdir(parents=True, exist_ok=True)
    return {"status": "created", "path": str(path)}


def schedule_desktop_folder_creation(
    name: str,
    time_hhmm: str,
    *,
    now: datetime | None = None,
    create_task_func=create_once_task,
) -> dict:
    target, note = target_datetime_for_time(time_hhmm, now=now)
    folder = desktop_dir() / safe_desktop_name(name)
    command = f'cmd.exe /c if not exist "{folder}" mkdir "{folder}"'
    task_fragment = f"Create_Desktop_Folder_{target.strftime('%Y%m%d_%H%M')}_{safe_desktop_name(name)[:32]}"
    task_result = create_task_func(task_fragment, target.strftime("%H:%M"), target.strftime("%d/%m/%Y"), command)
    status = "scheduled" if int(task_result.get("returncode", 1)) == 0 else "failed"
    return {
        "status": status,
        "task_name": f"Eve_{task_fragment}",
        "scheduled_for": target.isoformat(),
        "folder": str(folder),
        "command": command,
        "note": note,
        "task_result": task_result,
    }
