from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ErrorMemoryItem:
    id: str
    source: str
    command_or_action: str
    error_type: str
    message: str
    traceback: str = ""
    recurrence_count: int = 1
    known_fix: str = ""
    lab_candidate_id: str = ""
    resolved: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_error(message: str, *, source: str = "unknown") -> str:
    lowered = message.lower()
    if "permission" in lowered or "access is denied" in lowered:
        return "permission"
    if "modulenotfounderror" in lowered or "not installed" in lowered:
        return "missing_dependency"
    if "timeout" in lowered:
        return "timeout"
    if "jsondecodeerror" in lowered or "expecting value" in lowered:
        return "corrupt_or_empty_json"
    if "verification" in lowered or "not verified" in lowered:
        return "verification_failed"
    return source or "unknown"


def make_error_item(source: str, command_or_action: str, message: str, **kwargs: Any) -> ErrorMemoryItem:
    return ErrorMemoryItem(
        id=f"err_{uuid.uuid4().hex[:12]}",
        source=source,
        command_or_action=command_or_action,
        error_type=kwargs.pop("error_type", classify_error(message, source=source)),
        message=message,
        **kwargs,
    )
