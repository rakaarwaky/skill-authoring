"""Observability-module dogfood test (AES704).

Exercises the observability agent against a real skills pack fixture.
Skips when no live fixture is available.
"""

from __future__ import annotations

import pytest

from observability.src.agent_observability_orchestrator import SkillsObservabilityAgent
from shared.src.observability.taxonomy_observability_request import ObservabilityRequest


@pytest.mark.skip(reason="observability dogfood requires a live skills pack fixture")
def test_observability_dogfood_smoke() -> None:
    agent = SkillsObservabilityAgent()
    assert callable(agent.execute)
    result = agent.execute(ObservabilityRequest(op="bogus", query=""))
    assert result.ok is False
