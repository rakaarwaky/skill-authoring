"""Maintenance-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the maintenance-side capabilities:
prune, purge, archive, restore.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.maintenance.contract_maintenance_protocol import (
    ISkillsArchiverProtocol,
    ISkillsPrunerProtocol,
    ISkillsPurgerProtocol,
    ISkillsRestorerProtocol,
)
from shared.src.maintenance.taxonomy_maintenance_constant import (
    MAINTENANCE_LOCK_FILENAME,
    MAINTENANCE_SIDECAR_FILENAME,
    PRUNE_TTL_DEFAULT_DAYS,
    PURGE_TTL_DEFAULT_DAYS,
)
from shared.src.maintenance.taxonomy_maintenance_entity import (
    MaintenanceRecord,
    PruneCandidate,
)
from shared.src.maintenance.taxonomy_maintenance_error import (
    MaintenanceError,
    SkillNotArchivedError,
)
from shared.src.maintenance.taxonomy_maintenance_vo import MaintenanceOpId
from shared.src.maintenance.taxonomy_maintenance_request import MaintenanceRequest
from shared.src.maintenance.taxonomy_maintenance_response import MaintenanceResponse
from shared.src.maintenance.utility_maintenance_core import (
    default_purge_ttl_days,
    default_prune_ttl_days,
    maintenance_lock_path,
    maintenance_sidecar_path,
)

#: Default idle TTL (days) before a skill is considered prunable (re-exported).
MAINTENANCE_PRUNE_TTL_DEFAULT_DAYS = PRUNE_TTL_DEFAULT_DAYS
#: Default idle TTL (days) before an archived skill is purged (re-exported).
MAINTENANCE_PURGE_TTL_DEFAULT_DAYS = PURGE_TTL_DEFAULT_DAYS
#: Maintenance sidecar filename (re-exported).
MAINTENANCE_SIDECAR_FILENAME_EXPORT = MAINTENANCE_SIDECAR_FILENAME
#: Maintenance lock filename (re-exported).
MAINTENANCE_LOCK_FILENAME_EXPORT = MAINTENANCE_LOCK_FILENAME

#: Default prune TTL from the shared maintenance utility (genuine use).
DEFAULT_PRUNE_TTL_DAYS = default_prune_ttl_days()
#: Default purge TTL from the shared maintenance utility (genuine use).
DEFAULT_PURGE_TTL_DAYS = default_purge_ttl_days()

__all__ = [
    "DEFAULT_PRUNE_TTL_DAYS",
    "DEFAULT_PURGE_TTL_DAYS",
    "ISkillsArchiverProtocol",
    "ISkillsMaintenanceAggregate",
    "ISkillsPrunerProtocol",
    "ISkillsPurgerProtocol",
    "ISkillsRestorerProtocol",
    "MAINTENANCE_LOCK_FILENAME_EXPORT",
    "MAINTENANCE_PRUNE_TTL_DEFAULT_DAYS",
    "MAINTENANCE_PURGE_TTL_DEFAULT_DAYS",
    "MAINTENANCE_SIDECAR_FILENAME_EXPORT",
    "MaintenanceError",
    "MaintenanceOpId",
    "MaintenanceRecord",
    "PruneCandidate",
    "SkillNotArchivedError",
]


class ISkillsMaintenanceAggregate(ABC):
    """Single entry point over maintenance-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: MaintenanceRequest) -> MaintenanceResponse:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...

_layer_symbols = {
    "ISkillsArchiverProtocol": ISkillsArchiverProtocol,
    "ISkillsMaintenanceAggregate": ISkillsMaintenanceAggregate,
    "ISkillsPurgerProtocol": ISkillsPurgerProtocol,
    "ISkillsPrunerProtocol": ISkillsPrunerProtocol,
    "ISkillsRestorerProtocol": ISkillsRestorerProtocol,
    "MaintenanceError": MaintenanceError,
    "MaintenanceOpId": MaintenanceOpId,
    "MaintenanceRecord": MaintenanceRecord,
    "PruneCandidate": PruneCandidate,
    "SkillNotArchivedError": SkillNotArchivedError,
}
