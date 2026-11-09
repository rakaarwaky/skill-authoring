"""Observability-module smoke test (AES704).

Smoke-checks the observability agent's public surface.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import SkillsObservabilityAgent


def test_observability_smoke_surface() -> None:
    agent = SkillsObservabilityAgent()
    assert callable(agent.execute)
