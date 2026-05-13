from __future__ import annotations


def classify_learning_item(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ("sandro", "meu treino", "minha idade", "meus gostos")):
        return "sandro"
    if any(word in lower for word in ("gosto", "prefiro", "personalidade", "identidade")):
        return "personality"
    if any(word in lower for word in ("modelo", "agent", "paper", "github", "openai", "anthropic", "embedding", "browser")):
        return "technology"
    if any(word in lower for word in ("projeto", "repo", "rpg maker", "unreal")):
        return "project"
    return "world"
