"""Maintenance-module smoke test (AES704).

Smoke-checks the maintenance agent's public surface.
"""

from __future__ import annotations

from maintenance.src.agent_maintenance_orchestrator import SkillsMaintenanceAgent


def test_maintenance_smoke_surface() -> None:
    agent = SkillsMaintenanceAgent()
    assert callable(agent.execute)
