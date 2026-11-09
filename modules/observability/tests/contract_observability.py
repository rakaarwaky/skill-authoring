"""Observability-module contract test (AES704).

Verifies that ObservabilityAgent implements IObservabilityAggregate.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import ObservabilityAgent
from shared.src.observability.contract_observability_aggregate import (
    IObservabilityAggregate,
)


def test_observability_agent_implements_aggregate() -> None:
    agent = ObservabilityAgent()
    assert isinstance(agent, IObservabilityAggregate)
