"""Observability-module unit test (AES704).

Verifies the agent's unknown-op handling and error propagation.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import ObservabilityAgent
from shared.src.design.taxonomy_design_request import SkillsRequest
from shared.src.design.taxonomy_design_response import SkillsExitCode


def test_unknown_op_returns_usage_error() -> None:
    agent = ObservabilityAgent()
    result = agent.execute(SkillsRequest(op="bogus", query=""))
    assert result.ok is False
    assert result.exit_code == SkillsExitCode.USAGE_ERROR
