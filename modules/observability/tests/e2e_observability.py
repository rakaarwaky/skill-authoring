"""Observability-module e2e test (AES704).

End-to-end check of observability agent lifecycle behavior.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import ObservabilityAgent
from shared.src.design.taxonomy_design_request import SkillsRequest


def test_observability_e2e_lifecycle() -> None:
    agent = ObservabilityAgent()
    assert callable(agent.execute)
    result = agent.execute(SkillsRequest(op="bogus", query=""))
    assert result.ok is False
