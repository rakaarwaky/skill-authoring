"""Observability-module e2e test (AES704).

End-to-end check of observability agent lifecycle behavior.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import SkillsObservabilityAgent
from shared.src.observability.taxonomy_observability_request import ObservabilityRequest


def test_observability_e2e_lifecycle() -> None:
    agent = SkillsObservabilityAgent()
    assert callable(agent.execute)
    result = agent.execute(ObservabilityRequest(op="bogus", query=""))
    assert result.ok is False
