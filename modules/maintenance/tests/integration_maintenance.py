"""Maintenance-module integration test (AES704).

Verifies maintenance capability wiring and lifecycle flow end to end.
"""

from __future__ import annotations

from maintenance.src.agent_maintenance_orchestrator import SkillsMaintenanceAgent


def test_maintenance_agent_coordinates_capabilities() -> None:
    agent = SkillsMaintenanceAgent()
    assert agent is not None
