"""Stateless helpers for reading telemetry sidecars and usage artifacts.

Owned by the observability shared kernel; consumed by the telemetry
capability (``SkillsTelemetry.fold_used_count_into_sidecar``) and any
other module that needs to read the centralized ``.usage.json`` sidecar
or a run-dir ``usage.json`` artifact without importing a sibling
capability.
"""

from __future__ import annotations

import json
from pathlib import Path


def read_telemetry(path: str | Path) -> dict:
    """Read a telemetry JSON file (e.g. ``.usage.json`` sidecar).

    Returns an empty dict when the file is missing or unreadable.
    Sidecar values that are not dicts are skipped, matching the old
    ``_write_usage`` filter behavior.
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
    return {k: v for k, v in data.items() if isinstance(v, dict)}


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
