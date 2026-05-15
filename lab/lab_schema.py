from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class LabCandidateStatus(str, Enum):
    IDEA = "idea"
    PLANNED = "planned"
    RUNNING = "running"
    TESTED = "tested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class LabCandidate:
    id: str
    title: str
    hypothesis: str
    source: str
    point_id: int | None = None
    risk: str = "low"
    expected_metric: str = "manual_review"
    status: LabCandidateStatus = LabCandidateStatus.IDEA
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


def new_lab_candidate(title: str, hypothesis: str, source: str, **kwargs: Any) -> LabCandidate:
    return LabCandidate(id=f"lab_{uuid.uuid4().hex[:12]}", title=title, hypothesis=hypothesis, source=source, **kwargs)
