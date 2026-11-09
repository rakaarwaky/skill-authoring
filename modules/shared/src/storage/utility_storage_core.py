"""Storage-domain utility functions — stateless, pure, domain-agnostic.

Module-level functions only — no classes, no state. Used by the pack
bootstrap and skill-pack reader capabilities across the storage feature.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.storage.taxonomy_storage_constant import (
    PACK_MANIFEST_FILENAME,
    USAGE_LOCK_FILENAME,
    USAGE_SIDECAR_FILENAME,
)


def default_pack_root() -> Path:
    """Return the repo's ``skills/`` pack (the SSOT for all skills)."""
    return Path(__file__).resolve().parents[7]


def pack_manifest_path(pack_root: Path) -> Path:
    """Return the path to the pack manifest file."""
    return pack_root / PACK_MANIFEST_FILENAME


def usage_sidecar_path(skill_dir: Path) -> Path:
    """Return the path to a skill's usage sidecar file."""
    return skill_dir / USAGE_SIDECAR_FILENAME


def usage_lock_path(skill_dir: Path) -> Path:
    """Return the path to a skill's usage lock file."""
    return skill_dir / USAGE_LOCK_FILENAME


__all__ = [
    "default_pack_root",
    "pack_manifest_path",
    "usage_lock_path",
    "usage_sidecar_path",
]

_layer_symbols = {
    "default_pack_root": default_pack_root,
    "pack_manifest_path": pack_manifest_path,
    "usage_lock_path": usage_lock_path,
    "usage_sidecar_path": usage_sidecar_path,
}
