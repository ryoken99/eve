from __future__ import annotations

from autonomy.scheduler import list_scheduled_tasks
from computer.ocr import ocr_status
from computer.vision import monitor_report
from core.awareness_engine import collect_awareness
from security.safety_modes import describe_safety
from tools.mobile_bridge import bridge_status
from tools.windows_scheduler import list_eve_tasks


def render_dashboard() -> str:
    awareness = collect_awareness()
    monitors = monitor_report()
    ocr = ocr_status()
    local_tasks = list_scheduled_tasks()
    windows_tasks = list_eve_tasks()
    return "\n".join(
        [
            "EVE DASHBOARD",
            "",
            f"Modo: {awareness['eve']['mode']}",
            f"Tarefa: {awareness['eve']['active_task']}",
            f"Janela ativa: {awareness['desktop']['active_window']}",
            f"Monitores: {len(monitors['monitors'])} | Bounds: {monitors['virtual_bounds']}",
            f"OCR: {'OK' if ocr['available'] else 'FALHA'} | {ocr.get('path') or ocr.get('error')}",
            f"Agenda local: {len(local_tasks)} tarefa(s)",
            f"Tarefas Windows Eve: {len(windows_tasks.get('tasks', []))}",
            f"Mobile bridge: {bridge_status()['bridge_dir']}",
            "",
            "Seguranca:",
            describe_safety(),
        ]
    )
