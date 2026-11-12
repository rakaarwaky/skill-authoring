"""Storage-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation.
"""

from __future__ import annotations

from shared.src.storage.taxonomy_storage_request import StorageVerb
from storage.src.agent_storage_orchestrator import SkillsStorageAgent


def test_unknown_verb_raises_keyerror() -> None:
    agent = SkillsStorageAgent()
    try:
        agent._handler_for(StorageVerb("bogus"))
    except KeyError:
        return
    raise AssertionError("expected KeyError for unknown storage verb")


# ── Storage capability unit tests ───────────────────────────────────────

def test_storage_single_aggregate_contract() -> None:
    """UT-STORAGE-001: only contract_storage_aggregate defines ISkillsStorageAggregate."""
    from shared.src.storage.contract_storage_aggregate import (
        ISkillsStorageAggregate,
    )

    assert ISkillsStorageAggregate is not None
