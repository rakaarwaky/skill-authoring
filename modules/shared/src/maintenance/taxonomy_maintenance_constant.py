"""Maintenance-domain constants (AES taxonomy layer).

Constants consumed by the prune capability (archive idle, purge old
archives), archive, and restore capabilities: TTL defaults, lock
filenames, and maintenance sidecar keys.

Pure literals only — no functions, no I/O.
"""

from __future__ import annotations

from typing import Final

#: Default idle TTL in days before a skill is considered prunable (archived).
PRUNE_TTL_DEFAULT_DAYS: Final = 30

#: Default TTL in days an archived skill lives in the archive before purge.
PURGE_TTL_DEFAULT_DAYS: Final = 60

#: Default maintenance TTL defaults consumed by the prune capability.
_MAINTENANCE_TTL_DEFAULTS: Final[tuple] = (
    PRUNE_TTL_DEFAULT_DAYS,
    PURGE_TTL_DEFAULT_DAYS,
)

#: Sidecar file holding prune decision records.
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
