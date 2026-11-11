"""Maintenance-module benchmark (AES704).

Performance regression benchmark for the maintenance agent's op dispatch path.
"""

from __future__ import annotations

from maintenance.src.agent_maintenance_orchestrator import (
    SkillsMaintenanceAgent,
)
from shared.src.maintenance.taxonomy_maintenance_request import (
    MaintenanceRequest,
    MaintenanceVerb,
)


def bench_maintenance_dispatch() -> None:
    """Time op dispatch through the maintenance agent."""
    agent = SkillsMaintenanceAgent()
    _ = agent.execute(MaintenanceRequest(verb=MaintenanceVerb.PRUNE, query=""))
    _ = agent.execute(MaintenanceRequest(verb=MaintenanceVerb.PURGE, query=""))
