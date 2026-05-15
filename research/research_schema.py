from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ResearchDecision(str, Enum):
    APPLY_NOW = "apply_now"
    TEST_IN_LAB = "test_in_lab"
    WATCH = "watch"
    IGNORE = "ignore"


@dataclass(frozen=True)
class ResearchItem:
    title: str
    source: str
    url: str
    summary: str
    category: str = "technology"
    relevance_to_sandro: float = 0.0
    relevance_to_eve: float = 0.0
    novelty: float = 0.0
    actionability: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchTrack:
    id: str
    sources: list[str]
    queries: list[str]
    categories: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_research_item(item: ResearchItem | dict[str, Any]) -> dict[str, Any]:
    data = item.as_dict() if isinstance(item, ResearchItem) else dict(item)
    score = (
        float(data.get("relevance_to_sandro") or 0) * 0.25
        + float(data.get("relevance_to_eve") or 0) * 0.35
        + float(data.get("novelty") or 0) * 0.2
        + float(data.get("actionability") or 0) * 0.2
    )
    decision = ResearchDecision.IGNORE
    if score >= 0.75:
        decision = ResearchDecision.TEST_IN_LAB
    elif score >= 0.45:
        decision = ResearchDecision.WATCH
    return {"score": round(score, 3), "decision": decision.value, "item": data}
