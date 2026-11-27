"""Stateless helpers for reading the pack usage file and run-dir artifacts.

Owned by the observability shared kernel; consumed by the usage capability
(``SkillsObservabilityUsage.fold_used_count_into_usage``) and any other
module that needs to read the pack ``usage.json`` (flat ``items[]``) or a
run-dir ``usage.json`` artifact without importing a sibling capability.
"""

from __future__ import annotations

import json
from pathlib import Path


def read_telemetry(path: str | Path) -> dict:
    """Read the pack ``usage.json``; return its ``items`` keyed by name.

    Returns an empty dict when the file is missing or unreadable. Each
    entry in the returned mapping is a full item dict.
    """
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    items = data.get("items")
    if not isinstance(items, list):
        return {}
    return {i["name"]: i for i in items if isinstance(i, dict) and "name" in i}


def load_usage_sidecar(run_dir: str | Path) -> dict:
    """Load ``usage.json`` from *run_dir*.

    Returns an empty dict when the file is missing or unreadable.
    Reads the whole artifact (unlike ``read_telemetry`` which filters
    non-dict sidecar values) because ``usage.json`` carries list-valued
    keys such as ``items`` that the fold logic depends on.
    """
    p = Path(run_dir) / "usage.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


__all__ = [
    "load_usage_sidecar",
    "read_telemetry",
]
