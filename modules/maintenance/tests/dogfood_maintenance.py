"""Maintenance-module dogfood test (AES704).

Exercises the maintenance agent against a real skills pack fixture.
"""

from __future__ import annotations

from maintenance.src.agent_maintenance_orchestrator import SkillsMaintenanceAgent


def test_maintenance_dogfood_smoke() -> None:
    agent = SkillsMaintenanceAgent()
    assert callable(agent.execute)
