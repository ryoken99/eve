from __future__ import annotations


def infer_root_cause(error_text: str) -> dict:
    lower = error_text.lower()
    if "filenotfound" in lower or "no such file" in lower:
        cause = "missing file or wrong path"
    elif "permission" in lower or "access is denied" in lower:
        cause = "permission denied"
    elif "importerror" in lower or "modulenotfound" in lower:
        cause = "missing dependency or import path"
    elif "assert" in lower:
        cause = "behavior regression"
    else:
        cause = "unknown"
    return {"root_cause": cause, "lesson": f"Prevent future errors of type: {cause}", "prevention_rule": cause}
