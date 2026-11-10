"""Storage-module contract test (AES704).

Verifies that SkillsStorageAgent implements ISkillsStorageAggregate.
"""

from __future__ import annotations

from shared.src.storage.contract_storage_aggregate import ISkillsStorageAggregate
from storage.src.agent_storage_orchestrator import SkillsStorageAgent


def test_agent_implements_protocol() -> None:
    agent = SkillsStorageAgent()
    assert isinstance(agent, ISkillsStorageAggregate)
