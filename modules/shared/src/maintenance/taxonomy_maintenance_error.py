"""Maintenance-domain errors (AES taxonomy layer).

Typed errors used by the prune, purge, archive, and restore capabilities.
All errors extend ``SkillsError`` from the common layer.

No I/O, no imports from capabilities, agent, surface, root, or contract layers.
"""

from __future__ import annotations

from shared.src.common.taxonomy_common_error import (
    SkillsError,
    SkillsUsageError,
)
from shared.src.common.taxonomy_common_vo import ErrorMessage


class MaintenanceError(SkillsError):
    """Base for maintenance-domain failures."""

    def __init__(self, message: ErrorMessage, *, exit_code: int = 2) -> None:
        super().__init__(message, exit_code=exit_code)


class SkillNotArchivedError(SkillsUsageError):
    """The skill is not archived and cannot be purged."""


class PruneEmptyError(SkillsUsageError):
    """No idle skills matched the prune criteria."""


class PurgeEmptyError(SkillsUsageError):
    """No archived skills matched the purge criteria."""


__all__ = [
    "MaintenanceError",
    "PruneEmptyError",
    "PurgeEmptyError",
    "SkillNotArchivedError",
]

_layer_symbols = {
    "MaintenanceError": MaintenanceError,
    "PruneEmptyError": PruneEmptyError,
    "PurgeEmptyError": PurgeEmptyError,
    "SkillNotArchivedError": SkillNotArchivedError,
}
