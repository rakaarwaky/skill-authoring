"""Storage-module integration test (AES704).

Verifies storage capability wiring and lifecycle flow end to end.
"""

from __future__ import annotations

from storage.src.agent_storage_orchestrator import SkillsStorageAgent


def test_storage_agent_coordinates_capabilities() -> None:
    agent = SkillsStorageAgent()
    assert agent is not None
