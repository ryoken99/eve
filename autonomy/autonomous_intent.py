from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class AutonomousPriority(str, Enum):
    URGENT = "urgent"
    USEFUL = "useful"
    MAINTENANCE = "maintenance"
    RESEARCH = "research"
    DREAM = "dream"
    IMPROVEMENT = "improvement"
    COMMUNICATION = "communication"


@dataclass(frozen=True)
class AutonomousIntent:
    kind: AutonomousPriority
    source: str
    reason_to_act: str
    reason_not_to_act: str
    expected_value: float
    risk: str
    required_tools: list[str] = field(default_factory=list)
    target_point_id: int | None = None
    id: str = field(default_factory=lambda: f"intent_{uuid.uuid4().hex[:12]}")

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        return data


def rank_autonomous_intents(intents: list[AutonomousIntent]) -> list[dict[str, Any]]:
    risk_penalty = {"low": 0.0, "medium": 0.2, "high": 0.5, "dangerous": 1.0}
    rows = []
    for intent in intents:
        data = intent.as_dict()
        data["priority_score"] = round(float(intent.expected_value) - risk_penalty.get(intent.risk, 0.3), 3)
        rows.append(data)
    return sorted(rows, key=lambda item: item["priority_score"], reverse=True)
