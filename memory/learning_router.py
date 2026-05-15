from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from core.paths import MEMORY_DIR, ensure_project_dirs


class LearningCategory(str, Enum):
    WORLD = "world"
    TECHNOLOGY = "technology"
    SANDRO = "sandro"
    EVE = "eve"
    PROJECTS = "projects"
    SKILLS = "skills"
    ERRORS = "errors"
    RESEARCH = "research"
    RELATIONSHIPS = "relationships"


TARGET_FILES = {
    LearningCategory.WORLD: MEMORY_DIR / "world" / "world_learning.md",
    LearningCategory.TECHNOLOGY: MEMORY_DIR / "technology" / "technology_learning.md",
    LearningCategory.SANDRO: MEMORY_DIR / "long_term" / "sandro_profile.md",
    LearningCategory.EVE: MEMORY_DIR / "personality" / "personality_learning.md",
    LearningCategory.PROJECTS: MEMORY_DIR / "projects" / "project_learning.md",
    LearningCategory.SKILLS: MEMORY_DIR / "procedural" / "skill_learning.md",
    LearningCategory.ERRORS: MEMORY_DIR / "errors" / "error_learning.md",
    LearningCategory.RESEARCH: MEMORY_DIR / "technology" / "research_candidates.md",
    LearningCategory.RELATIONSHIPS: MEMORY_DIR / "long_term" / "relationship_learning.md",
}


@dataclass(frozen=True)
class LearningRoute:
    category: LearningCategory
    path: Path
    reason: str
    confidence: float


def classify_learning_item(text: str, metadata: dict[str, Any] | None = None) -> LearningRoute:
    metadata = metadata or {}
    lowered = text.lower()
    if metadata.get("category") in LearningCategory._value2member_map_:
        category = LearningCategory(metadata["category"])
        return LearningRoute(category, TARGET_FILES[category], "metadata category", 0.9)
    rules = [
        (LearningCategory.ERRORS, ("erro", "traceback", "failed", "falhou", "exception")),
        (LearningCategory.TECHNOLOGY, ("openai", "anthropic", "model", "github", "paper", "ai", "ia")),
        (LearningCategory.RESEARCH, ("research", "paper", "arxiv", "fonte", "source")),
        (LearningCategory.PROJECTS, ("projeto", "jogo", "livro", "eve", "helix")),
        (LearningCategory.SANDRO, ("sandro", "mestre", "gosto", "prefiro", "karate", "jiu-jitsu")),
        (LearningCategory.EVE, ("eu sinto", "eu gosto", "preferencia da eve", "personalidade")),
        (LearningCategory.SKILLS, ("skill", "procedimento", "como fazer")),
        (LearningCategory.RELATIONSHIPS, ("bubu", "marta", "amigo", "familia")),
    ]
    for category, terms in rules:
        if any(term in lowered for term in terms):
            return LearningRoute(category, TARGET_FILES[category], f"matched {category.value} terms", 0.7)
    return LearningRoute(LearningCategory.WORLD, TARGET_FILES[LearningCategory.WORLD], "default world knowledge", 0.4)


def route_learning_item(text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_project_dirs()
    route = classify_learning_item(text, metadata)
    route.path.parent.mkdir(parents=True, exist_ok=True)
    with route.path.open("a", encoding="utf-8") as handle:
        handle.write(f"- {text.strip()} [reason: {route.reason}; confidence={route.confidence}]\n")
    return {"category": route.category.value, "path": str(route.path), "reason": route.reason, "confidence": route.confidence}
