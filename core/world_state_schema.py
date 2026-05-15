from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorldState:
    timestamp: str
    timezone: str
    active_pc: str
    active_window: str
    active_app: str
    system_status: dict[str, Any] = field(default_factory=dict)
    autonomy_status: dict[str, Any] = field(default_factory=dict)
    recent_tasks: list[dict[str, Any]] = field(default_factory=list)
    current_user_context: dict[str, Any] = field(default_factory=dict)
    computer_use_observation: dict[str, Any] = field(default_factory=dict)
    admin_status: dict[str, Any] = field(default_factory=dict)
    memory_status: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
