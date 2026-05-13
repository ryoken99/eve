from __future__ import annotations

from memory.errors.error_analyzer import error_signature
from memory.errors.root_cause import infer_root_cause


def propose_regression_test(error_text: str) -> dict:
    cause = infer_root_cause(error_text)
    signature = error_signature(error_text)
    return {
        "error_signature": signature,
        "root_cause": cause["root_cause"],
        "lesson": cause["lesson"],
        "test_name": f"test_prevent_error_{signature}",
        "test_to_add": f"assert_prevents('{cause['prevention_rule']}')",
    }
