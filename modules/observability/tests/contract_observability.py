"""Observability-module contract test (AES704).

Verifies that SkillsObservabilityAgent implements ISkillsObservabilityAggregate.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import SkillsObservabilityAgent
from shared.src.observability.contract_observability_aggregate import (
    ISkillsObservabilityAggregate,
)


def test_observability_agent_implements_aggregate() -> None:
    agent = SkillsObservabilityAgent()
    assert isinstance(agent, ISkillsObservabilityAggregate)
