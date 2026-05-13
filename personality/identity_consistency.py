from __future__ import annotations

from personality.value_system import core_values


def identity_consistency_check(statement: str) -> dict:
    lower = statement.lower()
    conflicts = []
    if "fingir" in lower and "gosto" in lower:
        conflicts.append("nao fingir gostos")
    if "sem aprovacao" in lower or "sem aprovação" in lower:
        conflicts.append("seguranca")
    return {"consistent": not conflicts, "conflicts": conflicts, "values": core_values()}
