from __future__ import annotations


def compare_metric(baseline: float, variant: float, *, higher_is_better: bool = True) -> dict:
    delta = variant - baseline
    improved = delta > 0 if higher_is_better else delta < 0
    return {"baseline": baseline, "variant": variant, "delta": round(delta, 4), "improved": improved}
