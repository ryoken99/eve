from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


FALLBACK_ORDER = [
    "browser_dom",
    "browser_accessibility",
    "windows_uia",
    "app_specific_adapter",
    "keyboard_shortcut",
    "screenshot",
    "ocr",
    "coordinates",
]


class InterfaceTreeProvider(ABC):
    name = "base"

    @abstractmethod
    def observe(self, target: Any = None) -> dict[str, Any]:
        raise NotImplementedError


class BrowserDOMProvider(InterfaceTreeProvider):
    name = "browser_dom"

    def observe(self, target: Any = None) -> dict[str, Any]:
        return {"provider": self.name, "available": target is not None, "elements": []}


class BrowserAccessibilityProvider(InterfaceTreeProvider):
    name = "browser_accessibility"

    def observe(self, target: Any = None) -> dict[str, Any]:
        return {"provider": self.name, "available": target is not None, "elements": []}


class WindowsUIAProvider(InterfaceTreeProvider):
    name = "windows_uia"

    def observe(self, target: Any = None) -> dict[str, Any]:
        try:
            from computer.uia_observer import observe_uia_tree

            return observe_uia_tree()
        except Exception as exc:
            return {"provider": self.name, "available": False, "reason": f"{type(exc).__name__}: {exc}", "elements": []}


class VisualFallbackProvider(InterfaceTreeProvider):
    name = "visual_fallback"

    def observe(self, target: Any = None) -> dict[str, Any]:
        return {"provider": self.name, "available": True, "fallback_order": FALLBACK_ORDER[-3:], "elements": []}


def provider_priority() -> list[str]:
    return list(FALLBACK_ORDER)
