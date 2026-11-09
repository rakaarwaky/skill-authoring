"""Maintenance-domain capability contracts (AES contract layer, ABC traits).

One seam per maintenance-side capability: prune, purge, archive, restore.
Capabilities in ``modules/maintenance/src`` implement these; the
composition root injects them into the agent. No import of sibling
domain contracts — maintenance keeps its own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.common.taxonomy_common_vo import SkillName
from shared.src.maintenance.taxonomy_maintenance_request import SkillsRoot
from shared.src.maintenance.taxonomy_maintenance_response import MaintenanceResponse


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


class ISkillsArchiverProtocol(ABC):
    """Archive capability: move a live skill into ``_archive/``."""

    @abstractmethod
    def archive(self, skill: SkillName, root: SkillsRoot) -> MaintenanceResponse:
        """Move *skill* into the archive directory."""
        ...


class ISkillsRestorerProtocol(ABC):
    """Restore capability: bring an archived skill back to the live pack."""

    @abstractmethod
    def restore(self, skill: SkillName, root: SkillsRoot) -> MaintenanceResponse:
        """Restore *skill* from ``_archive/`` back to its live category."""
        ...


__all__ = [
    "ISkillsArchiverProtocol",
    "ISkillsPrunerProtocol",
    "ISkillsPurgerProtocol",
    "ISkillsRestorerProtocol",
]

_layer_symbols = {
    "ISkillsArchiverProtocol": ISkillsArchiverProtocol,
    "ISkillsPrunerProtocol": ISkillsPrunerProtocol,
    "ISkillsPurgerProtocol": ISkillsPurgerProtocol,
    "ISkillsRestorerProtocol": ISkillsRestorerProtocol,
}
