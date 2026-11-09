"""Maintenance-domain utility functions — stateless, pure, domain-agnostic.

Module-level functions only — no classes, no state. Used by the prune,
purge, archive, and restore capabilities across the maintenance feature.
"""

from __future__ import annotations

from pathlib import Path


def default_prune_ttl_days() -> int:
    """Return the default idle TTL (days) before a skill is prunable."""
    return 30


def default_purge_ttl_days() -> int:
    """Return the default idle TTL (days) before an archived skill is purged."""
    return 90


def maintenance_sidecar_path(skills_root: Path) -> Path:
    """Return the path to the pack-level maintenance sidecar."""
    return skills_root / ".maintenance.json"


def maintenance_lock_path(skills_root: Path) -> Path:
    """Return the path to the pack-level maintenance lock file."""
    return skills_root / ".maintenance.json.lock"


__all__ = [
    "default_prune_ttl_days",
    "default_purge_ttl_days",
    "maintenance_lock_path",
    "maintenance_sidecar_path",
]

_layer_symbols = {
    "default_purge_ttl_days": default_purge_ttl_days,
    "default_prune_ttl_days": default_prune_ttl_days,
    "maintenance_lock_path": maintenance_lock_path,
    "maintenance_sidecar_path": maintenance_sidecar_path,
}
