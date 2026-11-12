"""Maintenance-module contract test (AES704).

Verifies that SkillsMaintenanceAgent implements ISkillsMaintenanceAggregate.
"""

from __future__ import annotations

from maintenance.src.agent_maintenance_orchestrator import (
    SkillsMaintenanceAgent,
)
from shared.src.maintenance.contract_maintenance_aggregate import (
    ISkillsMaintenanceAggregate,
)


def test_agent_implements_protocol() -> None:
    agent = SkillsMaintenanceAgent()
    assert isinstance(agent, ISkillsMaintenanceAggregate)
