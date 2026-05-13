from __future__ import annotations

import hashlib
import re
from collections import defaultdict


def error_signature(text: str) -> str:
    normalized = re.sub(r"\d+", "<num>", text.lower())
    normalized = re.sub(r"[a-f0-9]{7,}", "<hash>", normalized)
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]


def cluster_errors_by_signature(errors: list[str]) -> dict:
    clusters: dict[str, list[str]] = defaultdict(list)
    for error in errors:
        clusters[error_signature(error)].append(error)
    return dict(clusters)


def detect_recurring_errors(errors: list[str], *, threshold: int = 2) -> dict:
    clusters = cluster_errors_by_signature(errors)
    return {signature: rows for signature, rows in clusters.items() if len(rows) >= threshold}
