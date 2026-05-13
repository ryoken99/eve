from __future__ import annotations

import re

NEGATION_RE = re.compile(r"\b(nao|não|never|not|no longer|ja nao|já não)\b", re.I)


def possible_conflict(left: str, right: str) -> dict:
    left_words = {word.lower() for word in re.findall(r"[\wÀ-ÿ]+", left) if len(word) > 3}
    right_words = {word.lower() for word in re.findall(r"[\wÀ-ÿ]+", right) if len(word) > 3}
    overlap = left_words & right_words
    negation_mismatch = bool(NEGATION_RE.search(left)) != bool(NEGATION_RE.search(right))
    return {"conflict": bool(overlap and negation_mismatch), "overlap": sorted(overlap), "negation_mismatch": negation_mismatch}
