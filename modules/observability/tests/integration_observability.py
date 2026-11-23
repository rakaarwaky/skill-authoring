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
    from observability.src.capabilities_observability_memory import SkillsObservabilityMemory

    memory = SkillsObservabilityMemory()
    run_dir = str(tmp_path / "memrun")
    memory.scan_memory(
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


def test_scan_sessions_usage_writes_usage_json(tmp_path) -> None:
    """IT-OBS-001: scan_sessions(action='usage') writes usage.json, not phrases.json."""
    import json
    from pathlib import Path

    from observability.src.capabilities_observability_usage import SkillsObservabilityUsage

    scan = SkillsPhraseScan()
    usage = SkillsObservabilityUsage()
    run_dir = str(tmp_path / "usage-run")
    # Empty grok_home — no sessions, but the scan still writes usage.json.
    scan_result = scan.scan_sessions(str(tmp_path / "grok"), run_dir)

    usage.write_usage("$HOME/.grok", run_dir, scan_result.records)

    assert (Path(run_dir) / "usage.json").is_file()
    assert not (Path(run_dir) / "phrases.json").exists()
    usage_data = json.loads((Path(run_dir) / "usage.json").read_text())
    assert "items" in usage_data
    assert "kept_sessions" in usage_data
