"""Maintenance-domain capability contracts (AES contract layer, ABC traits).

One seam per maintenance-side capability: prune, purge. Capabilities in
``modules/maintenance/src`` implement these; the composition root injects
them into the agent. No import of sibling domain contracts — maintenance
keeps its own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.common.taxonomy_common_vo import SkillName
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
    """Prune capability: bulk-archive idle skills past a days threshold."""

    @abstractmethod
    def prune(
        self,
        root: SkillsRoot | None = None,
        days: int | None = None,
        dry_run: bool = False,
    ) -> MaintenanceResponse:
        """Bulk-archive idle skills past *days*; *dry_run* reports only."""
        ...


class ISkillsPurgerProtocol(ABC):
    """Purge capability: delete archived skills past TTL or a named skill."""

    @abstractmethod
    def purge(
        self,
        skill: SkillName | None = None,
        root: SkillsRoot | None = None,
        dry_run: bool = False,
    ) -> MaintenanceResponse:
        """Purge archived skills past TTL, or the single named *skill*."""
        ...


__all__ = [
    "ISkillsPrunerProtocol",
    "ISkillsPurgerProtocol",
]

_layer_symbols = {
    "ISkillsPrunerProtocol": ISkillsPrunerProtocol,
    "ISkillsPurgerProtocol": ISkillsPurgerProtocol,
    "MAINTENANCE_LOCK_FILENAME": MAINTENANCE_LOCK_FILENAME,
    "MAINTENANCE_SIDECAR_FILENAME": MAINTENANCE_SIDECAR_FILENAME,
    "PRUNE_TTL_DEFAULT_DAYS": PRUNE_TTL_DEFAULT_DAYS,
    "PURGE_TTL_DEFAULT_DAYS": PURGE_TTL_DEFAULT_DAYS,
}
