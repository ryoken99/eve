from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ConsolidationSignalType(str, Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    PROJECT_UPDATE = "project_update"
    TASK = "task"
    ERROR = "error"
    IDEA = "idea"
    RELATIONSHIP = "relationship"
    TECHNICAL_DECISION = "technical_decision"
    FUTURE_FOLLOWUP = "future_followup"


@dataclass(frozen=True)
class ConsolidationInput:
    source: str = "diary"
    content: str = ""
    day: str = ""
    transcript_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConsolidationSignal:
    type: ConsolidationSignalType
    text: str
    signal_id: str = ""
    source: str = "diary"
    importance: float = 0.5
    recurrence: float = 0.0
    user_value: float = 0.5
    confidence: float = 0.6
    memory_destination: str = "medium_term"
    tags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["type"] = self.type.value
        return data

    def to_dict(self) -> dict[str, Any]:
        return self.as_dict()


@dataclass(frozen=True)
class ConsolidationDecision:
    signal: dict[str, Any] = field(default_factory=dict)
    action: str = "store"
    reason: str = ""
    signal_id: str = ""
    decision: str = "store"
    destination: str = "medium_term"
    confidence: float = 0.6

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConsolidationReport:
    report_id: str = ""
    inputs: list[dict[str, Any]] = field(default_factory=list)
    signals: list[ConsolidationSignal] = field(default_factory=list)
    decisions: list[ConsolidationDecision] = field(default_factory=list)
    day: str = ""
    input: ConsolidationInput = field(default_factory=ConsolidationInput)
    summary: str = ""
    generated_at: str = ""
    markdown_path: str = ""
    json_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "day": self.day,
            "input": asdict(self.input),
            "inputs": self.inputs,
            "signals": [signal.to_dict() if hasattr(signal, "to_dict") else signal for signal in self.signals],
            "decisions": [decision.to_dict() if hasattr(decision, "to_dict") else decision for decision in self.decisions],
            "summary": self.summary,
            "generated_at": self.generated_at,
            "markdown_path": self.markdown_path,
            "json_path": self.json_path,
        }
