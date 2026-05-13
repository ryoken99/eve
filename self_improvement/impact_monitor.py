from __future__ import annotations


def compare_impact(baseline_metric: float, new_metric: float, *, minimum_delta: float = 0.0) -> dict:
    delta = new_metric - baseline_metric
    return {"improved": delta >= minimum_delta, "baseline_metric": baseline_metric, "new_metric": new_metric, "delta": round(delta, 4)}
