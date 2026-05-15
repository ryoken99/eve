from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AppPermissionRule:
    app_name: str
    allowed_actions: list[str] = field(default_factory=list)
    requires_confirmation: list[str] = field(default_factory=list)
    blocked_actions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_app_permission_model() -> dict[str, Any]:
    return {
        "browser": AppPermissionRule(
            app_name="browser",
            allowed_actions=["read", "navigate", "search", "draft"],
            requires_confirmation=["post", "submit", "send"],
            blocked_actions=["purchase", "financial_trade"],
        ).as_dict(),
        "system": AppPermissionRule(
            app_name="system",
            allowed_actions=["observe", "read_state"],
            requires_confirmation=["admin", "install", "modify_startup"],
            blocked_actions=["delete_without_backup"],
        ).as_dict(),
    }
