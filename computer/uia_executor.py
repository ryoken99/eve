from __future__ import annotations

from computer.uia_observer import find_element


def invoke_element(element_id: str | None = None, *, name: str | None = None, control_type: str | None = None, tree: dict | None = None) -> dict:
    found = find_element(name=name, control_type=control_type, tree=tree)
    if not found.get("found"):
        return {"ok": False, "engine": "uia", "action": "invoke", "reason": "element not found", "query": found.get("query")}
    element = found["element"]
    if element_id and element.get("element_id") != element_id:
        return {"ok": False, "engine": "uia", "action": "invoke", "reason": "element_id mismatch", "element": element}
    return {"ok": True, "engine": "uia", "action": "invoke", "element": element, "simulated": True}


def type_into_element(text: str, *, name: str | None = None, control_type: str | None = None, tree: dict | None = None) -> dict:
    found = find_element(name=name, control_type=control_type, tree=tree)
    if not found.get("found"):
        return {"ok": False, "engine": "uia", "action": "type", "reason": "element not found", "query": found.get("query")}
    return {"ok": True, "engine": "uia", "action": "type", "element": found["element"], "text_length": len(text), "simulated": True}
