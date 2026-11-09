"""Maintenance-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the maintenance-side capabilities:
prune, purge.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.maintenance.contract_maintenance_protocol import (
    ISkillsPrunerProtocol,
    ISkillsPurgerProtocol,
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

__all__ = [
    "ISkillsMaintenanceAggregate",
    "ISkillsPrunerProtocol",
    "ISkillsPurgerProtocol",
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
    "ISkillsMaintenanceAggregate": ISkillsMaintenanceAggregate,
    "ISkillsPurgerProtocol": ISkillsPurgerProtocol,
    "ISkillsPrunerProtocol": ISkillsPrunerProtocol,
    "MaintenanceError": MaintenanceError,
    "MaintenanceOpId": MaintenanceOpId,
    "MaintenanceRecord": MaintenanceRecord,
    "PruneCandidate": PruneCandidate,
    "SkillNotArchivedError": SkillNotArchivedError,
}
