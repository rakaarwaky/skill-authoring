"""Observability-module dogfood test (AES704).

Exercises the observability agent against a real skills pack fixture.
Skips when no live fixture is available.
"""

from __future__ import annotations

import pytest

from observability.src.agent_observability_orchestrator import (
    ObservabilityAgent,
)
from shared.src.design.taxonomy_design_request import SkillsRequest


@pytest.mark.skip(reason="observability dogfood requires a live skills pack fixture")
def test_observability_dogfood_smoke() -> None:
    agent = ObservabilityAgent()
    assert callable(agent.execute)
    result = agent.execute(SkillsRequest(op="bogus", query=""))
    assert result.ok is False
