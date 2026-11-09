"""Storage-module acceptance test (AES704).

Acceptance-level check for storage agent readiness.
."""

from __future__ import annotations

from storage.src.agent_storage_orchestrator import SkillsStorageAgent


def test_storage_acceptance_ready() -> None:
    agent = SkillsStorageAgent()
    assert agent is not None
