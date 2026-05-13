from __future__ import annotations


def sandbox_result(candidate: dict) -> dict:
    tests = candidate.get("tests_required") or []
    compile_ok = candidate.get("compile_ok", True)
    return {"sandbox_ok": bool(tests) and compile_ok, "tests_required": tests, "compile_ok": compile_ok}
