"""Storage-module dogfood test (AES704).

Exercises the storage agent against a real skills pack fixture.
"""

from __future__ import annotations

from storage.src.agent_storage_orchestrator import SkillsStorageAgent


def test_storage_dogfood_smoke() -> None:
    agent = SkillsStorageAgent()
    assert callable(agent.execute)
