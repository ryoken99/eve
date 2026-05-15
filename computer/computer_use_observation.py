from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AppIdentity:
    app_name: str
    process_name: str = ""
    pid: int | None = None
    window_title: str = ""
    permission_status: str = "unknown"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UIElement:
    element_id: str
    name: str = ""
    role: str = ""
    control_type: str = ""
    automation_id: str = ""
    enabled: bool = True
    visible: bool = True
    offscreen: bool = False
    value: str = ""
    children: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StructuredInterfaceTree:
    provider: str
    app: dict[str, Any]
    root: dict[str, Any]
    elements: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ComputerUseObservation:
    app: dict[str, Any]
    tree: dict[str, Any]
    preferred_engine: str
    fallback_order: list[str]
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ActionPlan:
    goal: str
    target_app: str
    preferred_engine: str
    selector: dict[str, Any]
    expected_change: dict[str, Any]
    fallback_order: list[str]


@dataclass(frozen=True)
class ActionVerification:
    ok: bool
    expected_change: dict[str, Any]
    observed_change: dict[str, Any]
    evidence: list[str] = field(default_factory=list)
    reason: str = ""
