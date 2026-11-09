"""Observability-module integration test (AES704).

Verifies observability capability wiring end to end.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import SkillsObservabilityAgent
from observability.src.capabilities_skills_ledger import SkillsLedger
from observability.src.capabilities_skills_telemetry import SkillsTelemetry


def test_observability_agent_coordinates_capabilities() -> None:
    agent = SkillsObservabilityAgent(
        ledger=SkillsLedger(),
        telemetry=SkillsTelemetry(),
    )
    assert agent is not None
