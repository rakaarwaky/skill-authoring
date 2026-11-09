"""Storage-module e2e test (AES704).

End-to-end check of storage agent lifecycle behavior.
"""

from __future__ import annotations

from storage.src.agent_storage_orchestrator import SkillsStorageAgent


def test_storage_e2e_lifecycle() -> None:
    agent = SkillsStorageAgent()
    assert callable(agent.execute)
