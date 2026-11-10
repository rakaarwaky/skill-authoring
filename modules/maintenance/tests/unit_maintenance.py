"""Maintenance-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation.
"""

from __future__ import annotations

from shared.src.maintenance.taxonomy_maintenance_request import (
    MaintenanceRequest,
    MaintenanceVerb,
)
from shared.src.maintenance.taxonomy_maintenance_response import MaintenanceResponse

from maintenance.src.agent_maintenance_orchestrator import SkillsMaintenanceAgent


def test_unknown_verb_returns_usage_error() -> None:
    agent = SkillsMaintenanceAgent(prune=object(), purge=object())
    result = agent.execute(MaintenanceRequest(verb=MaintenanceVerb("bogus")))
    assert isinstance(result, MaintenanceResponse)
    assert result.ok is False
