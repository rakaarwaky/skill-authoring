"""Maintenance-domain capability contracts (AES contract layer, ABC traits).

One seam for the maintenance-side capability: prune. The prune
capability owns both archive-idle and purge-old-archive passes; the
composition root injects it into the agent. No import of sibling domain
contracts — maintenance keeps its own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.maintenance.taxonomy_maintenance_constant import (
    MAINTENANCE_LOCK_FILENAME,
    MAINTENANCE_SIDECAR_FILENAME,
    PRUNE_TTL_DEFAULT_DAYS,
    PURGE_TTL_DEFAULT_DAYS,
)
from shared.src.maintenance.taxonomy_maintenance_request import SkillsRoot
from shared.src.maintenance.taxonomy_maintenance_response import (
    MaintenanceResponse,
)


class ISkillsPrunerProtocol(ABC):
    """Prune capability: archive idle skills, then purge old archives."""

    @abstractmethod
    def prune(
        self,
        root: SkillsRoot | None = None,
        days: int | None = None,
        purge_days: int | None = None,
        dry_run: bool = False,
    ) -> MaintenanceResponse:
        """Archive idle skills past *days*; purge archived skills past *purge_days*."""
        ...


__all__ = [
    "ISkillsPrunerProtocol",
]

_layer_symbols = {
    "ISkillsPrunerProtocol": ISkillsPrunerProtocol,
    "MAINTENANCE_LOCK_FILENAME": MAINTENANCE_LOCK_FILENAME,
    "MAINTENANCE_SIDECAR_FILENAME": MAINTENANCE_SIDECAR_FILENAME,
    "PRUNE_TTL_DEFAULT_DAYS": PRUNE_TTL_DEFAULT_DAYS,
    "PURGE_TTL_DEFAULT_DAYS": PURGE_TTL_DEFAULT_DAYS,
}