from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from core.paths import PLUGINS_DIR, ensure_project_dirs
from security.audit_log import log_event


def plugin_manifest_path(plugin_dir: Path) -> Path:
    return plugin_dir / "plugin.json"


def discover_plugins() -> list[dict[str, Any]]:
    ensure_project_dirs()
    plugins: list[dict[str, Any]] = []
    for plugin_dir in sorted(path for path in PLUGINS_DIR.iterdir() if path.is_dir()):
        manifest_path = plugin_manifest_path(plugin_dir)
        manifest: dict[str, Any] = {"id": plugin_dir.name, "name": plugin_dir.name, "enabled": True}
        if manifest_path.exists():
            try:
                manifest.update(json.loads(manifest_path.read_text(encoding="utf-8")))
            except Exception as exc:
                manifest["load_error"] = f"{type(exc).__name__}: {exc}"
        manifest["path"] = str(plugin_dir)
        manifest["has_init"] = (plugin_dir / "__init__.py").exists()
        plugins.append(manifest)
    return plugins


def plugin_summary() -> dict[str, Any]:
    plugins = discover_plugins()
    return {
        "plugin_root": str(PLUGINS_DIR),
        "count": len(plugins),
        "enabled": [item["id"] for item in plugins if item.get("enabled", True)],
        "plugins": plugins,
    }


def load_plugin_module(plugin_id: str):
    plugin_dir = PLUGINS_DIR / plugin_id
    init_path = plugin_dir / "__init__.py"
    if not init_path.exists():
        raise FileNotFoundError(f"Plugin sem __init__.py: {plugin_id}")
    spec = importlib.util.spec_from_file_location(f"eve_plugin_{plugin_id}", init_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Nao consegui carregar plugin: {plugin_id}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    log_event("plugin_loaded", {"plugin_id": plugin_id, "path": str(init_path)})
    return module

