"""Storage-module smoke test (AES704).

Smoke-checks the storage agent's public surface.
"""

from __future__ import annotations

from storage.src.agent_storage_orchestrator import SkillsStorageAgent


def test_storage_smoke_surface() -> None:
    agent = SkillsStorageAgent()
    assert callable(agent.execute)
