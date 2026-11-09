"""Maintenance-domain constants (AES taxonomy layer).

Constants consumed by the prune, purge, archive, and restore capabilities:
TTL defaults, lock filenames, and maintenance sidecar keys.

Pure literals only — no functions, no I/O.
"""

from __future__ import annotations

from typing import Final

#: Default idle TTL in days before a skill is considered prunable.
PRUNE_TTL_DEFAULT_DAYS: Final = 30

#: Default idle TTL in days before an archived skill is purged.
PURGE_TTL_DEFAULT_DAYS: Final = 90

#: Sidecar file holding prune/purge decision records.
MAINTENANCE_SIDECAR_FILENAME: Final = ".maintenance.json"

#: Lock filename guarding concurrent maintenance operations.
MAINTENANCE_LOCK_FILENAME: Final = ".maintenance.json.lock"

__all__ = [
    "MAINTENANCE_LOCK_FILENAME",
    "MAINTENANCE_SIDECAR_FILENAME",
    "PRUNE_TTL_DEFAULT_DAYS",
    "PURGE_TTL_DEFAULT_DAYS",
]

_layer_symbols = {
    "MAINTENANCE_LOCK_FILENAME": MAINTENANCE_LOCK_FILENAME,
    "MAINTENANCE_SIDECAR_FILENAME": MAINTENANCE_SIDECAR_FILENAME,
    "PRUNE_TTL_DEFAULT_DAYS": PRUNE_TTL_DEFAULT_DAYS,
    "PURGE_TTL_DEFAULT_DAYS": PURGE_TTL_DEFAULT_DAYS,
}
