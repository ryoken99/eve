from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class PreferenceStatus(str, Enum):
    CANDIDATE = "candidate"
    REINFORCED = "reinforced"
    MATURE = "mature"
    REJECTED = "rejected"


@dataclass(frozen=True)
class PreferenceCandidate:
    topic: str
    evidence: list[str] = field(default_factory=list)
    sentiment: str = "curious"
    strength: float = 0.1
    confidence: float = 0.5
    status: PreferenceStatus = PreferenceStatus.CANDIDATE
    first_seen: str = ""
    last_seen: str = ""
    owner: str = "eve"

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class PersonalityTrait:
    name: str
    description: str
    strength: float = 0.5
    evidence_count: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
