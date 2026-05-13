from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from computer.active_window import get_active_window_title


@dataclass
class UIAElement:
    element_id: str
    name: str
    control_type: str
    automation_id: str = ""
    enabled: bool = True
    children: list[dict] | None = None


def uia_available() -> bool:
    try:
        import uiautomation  # type: ignore  # noqa: F401
        return True
    except Exception:
        return False


def _element_to_dict(control: Any, *, depth: int, max_depth: int, index: int = 0) -> dict:
    name = getattr(control, "Name", "") or ""
    control_type = getattr(control, "ControlTypeName", "") or type(control).__name__
    automation_id = getattr(control, "AutomationId", "") or ""
    row = asdict(UIAElement(f"{depth}:{index}:{automation_id or name or control_type}", name, control_type, automation_id))
    if depth < max_depth:
        children = []
        try:
            for child_index, child in enumerate(control.GetChildren()):
                children.append(_element_to_dict(child, depth=depth + 1, max_depth=max_depth, index=child_index))
        except Exception:
            children = []
        row["children"] = children
    return row


def dump_active_window_tree(*, max_depth: int = 3, root: Any | None = None) -> dict:
    if root is not None:
        return {"available": True, "engine": "uia", "active_window": get_active_window_title(), "tree": _element_to_dict(root, depth=0, max_depth=max_depth)}
    if not uia_available():
        return {"available": False, "engine": "uia", "active_window": get_active_window_title(), "tree": None, "reason": "uiautomation package not installed"}
    try:
        import uiautomation as auto  # type: ignore
        control = auto.GetForegroundControl()
        return {"available": True, "engine": "uia", "active_window": get_active_window_title(), "tree": _element_to_dict(control, depth=0, max_depth=max_depth)}
    except Exception as exc:
        return {"available": False, "engine": "uia", "active_window": get_active_window_title(), "tree": None, "error": str(exc)}


def iter_tree(node: dict | None):
    if not node:
        return
    yield node
    for child in node.get("children") or []:
        yield from iter_tree(child)


def find_element(name: str | None = None, control_type: str | None = None, automation_id: str | None = None, *, tree: dict | None = None) -> dict:
    snapshot = {"tree": tree} if tree else dump_active_window_tree()
    for node in iter_tree(snapshot.get("tree")):
        if name and name.lower() not in (node.get("name") or "").lower():
            continue
        if control_type and control_type.lower() not in (node.get("control_type") or "").lower():
            continue
        if automation_id and automation_id != node.get("automation_id"):
            continue
        return {"found": True, "element": node, "engine": "uia"}
    return {"found": False, "engine": "uia", "query": {"name": name, "control_type": control_type, "automation_id": automation_id}}
