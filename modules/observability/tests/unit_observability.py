"""Observability-module unit test (AES704).

Verifies the agent's unknown-op handling and error propagation.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import SkillsObservabilityAgent
from shared.src.observability.taxonomy_observability_request import ObservabilityRequest
from shared.src.observability.taxonomy_observability_response import ObservabilityExitCode


def test_unknown_op_returns_usage_error() -> None:
    agent = SkillsObservabilityAgent()
    result = agent.execute(ObservabilityRequest(op="bogus", query=""))
    assert result.ok is False
    assert result.exit_code == ObservabilityExitCode.USAGE_ERROR
