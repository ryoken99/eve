from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DreamType(str, Enum):
    MEMORY_CLEANUP = "memory_cleanup"
    PROJECT_REVIEW = "project_review"
    ERROR_REVIEW = "error_review"
    PERSONALITY_EVOLUTION = "personality_evolution"
    RESEARCH_REVIEW = "research_review"
    SELF_IMPROVEMENT = "self_improvement"
    CAPABILITY_REVIEW = "capability_review"


@dataclass(frozen=True)
class DreamReport:
    dream_id: str
    type: DreamType
    inputs: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    memory_updates: list[dict[str, Any]] = field(default_factory=list)
    lab_candidates: list[dict[str, Any]] = field(default_factory=list)
    followups: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["type"] = self.type.value
        return data


def new_dream_report(dream_type: DreamType, **kwargs: Any) -> DreamReport:
    return DreamReport(dream_id=f"dream_{uuid.uuid4().hex[:12]}", type=dream_type, **kwargs)
