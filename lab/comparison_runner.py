from __future__ import annotations

from lab.metrics import compare_metric


def run_comparison(baseline_fn, variant_fn, *, threshold: float = 0.0, higher_is_better: bool = True) -> dict:
    baseline = float(baseline_fn())
    variant = float(variant_fn())
    comparison = compare_metric(baseline, variant, higher_is_better=higher_is_better)
    accepted = comparison["improved"] and abs(comparison["delta"]) >= threshold
    return {"accepted": accepted, "comparison": comparison, "threshold": threshold}
