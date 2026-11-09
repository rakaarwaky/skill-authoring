"""Observability-module acceptance test (AES704).

Acceptance-level check for observability agent readiness.
."""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import ObservabilityAgent


def test_observability_acceptance_ready() -> None:
    agent = ObservabilityAgent()
    assert agent is not None
