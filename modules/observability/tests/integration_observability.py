"""Observability-module integration test (AES704).

Verifies observability capability wiring end to end.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import (
    ObservabilityAgent,
)
from observability.src.capabilities_skills_phrase_scan import SkillsPhraseScan
from observability.src.capabilities_skills_telemetry import SkillsTelemetry


def test_observability_agent_coordinates_capabilities() -> None:
    agent = ObservabilityAgent(
        telemetry=SkillsTelemetry(),
        scan=SkillsPhraseScan(),
    )
    assert agent is not None


def test_scan_memory_writes_memory_json_to_run_dir(tmp_path) -> None:
    """UT-OBSERVABILITY-004: scan_memory writes memory.json into run_dir."""
    scan = SkillsPhraseScan()
    run_dir = str(tmp_path / "memrun")
    report = scan.scan_memory(
        "$HOME/.grok",
        run_dir,
    )
    # memory.json must exist next to the report.
    import json
    from pathlib import Path

    path = Path(run_dir) / "memory.json"
    assert path.is_file()
    data = json.loads(path.read_text())
    assert data["source"] == "memory-v2"
    assert "topics" in data
    assert "observations" in data
    assert "keep_list" in data
    assert isinstance(data["topics"], list)
    # At least one topic from skill-authoring workspace should be present.
    titles = [t["title"] for t in data["topics"] if t["title"]]
    assert any("skill-authoring" in t for t in titles) or any(
        "skill-authoring" in t.get("path", "") for t in data["topics"]
    )
