"""Observability-module contract test (AES704).

Verifies that SkillsObservabilityAgent implements ISkillsObservabilityAggregate
and SkillsPhraseAgent implements ISkillsTracesAggregate.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import SkillsObservabilityAgent
from observability.src.agent_skills_phrase_orchestrator import SkillsPhraseAgent
from shared.src.observability.contract_observability_aggregate import (
    ISkillsObservabilityAggregate,
)
from shared.src.observability.contract_observability_protocol import ISkillsTracesProtocol


def test_observability_agent_implements_aggregate() -> None:
    agent = SkillsObservabilityAgent()
    assert isinstance(agent, ISkillsObservabilityAggregate)


def test_phrase_agent_implements_protocol() -> None:
    agent = SkillsPhraseAgent()
    assert isinstance(agent, ISkillsTracesProtocol)
