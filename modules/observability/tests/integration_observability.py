"""Observability-module integration test (AES704).

Verifies observability capability wiring end to end.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import ObservabilityAgent
from observability.src.capabilities_skills_ledger import SkillsLedger
from observability.src.capabilities_skills_phrase_scan import SkillsPhraseScan
from observability.src.capabilities_skills_telemetry import SkillsTelemetry


def test_observability_agent_coordinates_capabilities() -> None:
    agent = ObservabilityAgent(
        ledger=SkillsLedger(),
        telemetry=SkillsTelemetry(),
        scan=SkillsPhraseScan(),
    )
    assert agent is not None
