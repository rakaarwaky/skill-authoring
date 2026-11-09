"""Observability-module benchmark (AES704).

Performance regression benchmark for the observability agent's op dispatch path.
Side-effect free: dispatches an unknown op so no capability I/O is exercised.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import SkillsObservabilityAgent
from shared.src.observability.taxonomy_observability_request import ObservabilityRequest


def bench_observability_dispatch() -> None:
    """Time op dispatch through the observability agent."""
    agent = SkillsObservabilityAgent()
    _ = agent.execute(ObservabilityRequest(op="bogus", query=""))
