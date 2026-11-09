"""Observability-module smoke test (AES704).

Smoke-checks the observability agent's public surface.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import ObservabilityAgent


def test_observability_smoke_surface() -> None:
    agent = ObservabilityAgent()
    assert callable(agent.execute)
