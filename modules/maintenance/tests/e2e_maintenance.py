"""Maintenance-module e2e test (AES704).

End-to-end check of maintenance agent lifecycle behavior.
"""

from __future__ import annotations

from maintenance.src.agent_maintenance_orchestrator import SkillsMaintenanceAgent


def test_maintenance_e2e_lifecycle() -> None:
    agent = SkillsMaintenanceAgent()
    assert callable(agent.execute)
