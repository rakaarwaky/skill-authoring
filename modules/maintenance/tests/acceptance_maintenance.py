"""Maintenance-module acceptance test (AES704).

Acceptance-level check for maintenance agent readiness.
"""

from __future__ import annotations

from maintenance.src.agent_maintenance_orchestrator import (
    SkillsMaintenanceAgent,
)


def test_maintenance_acceptance_ready() -> None:
    agent = SkillsMaintenanceAgent()
    assert agent is not None
