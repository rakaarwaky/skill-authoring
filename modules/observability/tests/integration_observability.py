"""Observability-module integration test (AES704).

Verifies observability capability wiring end to end.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import (
    ObservabilityAgent,
)
from observability.src.capabilities_skills_phrase_scan import SkillsPhraseScan
from observability.src.capabilities_skills_telemetry import SkillsTelemetry
from shared.src.design.taxonomy_design_request import SkillsOp, SkillsRequest


def test_observability_agent_coordinates_capabilities() -> None:
    agent = ObservabilityAgent(
        telemetry=SkillsTelemetry(),
        scan=SkillsPhraseScan(),
    )
    assert agent is not None


def test_scan_sessions_usage_writes_usage_json(tmp_path, monkeypatch) -> None:
    """IT-OBS-001: Full agent flow — scan_sessions → write_usage → fold_used_count_into_sidecar writes usage.json."""
    import json
    from pathlib import Path

    from observability.src.capabilities_observability_usage import (
        SkillsObservabilityUsage,
    )
    from shared.src.maintenance.utility_lifecycle_support import pack_usage_path

    agent = ObservabilityAgent(
        telemetry=SkillsTelemetry(),
        scan=SkillsPhraseScan(),
        usage=SkillsObservabilityUsage(),
    )
    run_dir = str(tmp_path / "usage-run")
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    grok_home = str(tmp_path / "grok")
    sidecar = tmp_path / ".usage.json"
    monkeypatch.setattr(
        "observability.src.capabilities_skills_telemetry.pack_usage_path",
        lambda pack_root=None: sidecar,
    )

    # Exercise the agent's usage path: scan sessions → write usage.json → fold into sidecar.
    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={
                "traces_action": "usage",
                "grok_home": grok_home,
                "run_dir": run_dir,
            },
        )
    )

    assert result.ok
    usage_path = Path(run_dir) / "usage.json"
    assert usage_path.is_file()
    usage_data = json.loads(usage_path.read_text())
    assert "items" in usage_data
    assert "kept_sessions" in usage_data
    assert not (Path(run_dir) / "phrase.json").exists()


def test_agent_routes_usage_traces_to_write_usage_and_telemetry(tmp_path, monkeypatch) -> None:
    """IT-OBS-002: Agent routes TRACES usage action to write_usage + fold_used_count_into_sidecar."""
    import json
    from pathlib import Path

    from observability.src.capabilities_observability_usage import (
        SkillsObservabilityUsage,
    )
    from shared.src.maintenance.utility_lifecycle_support import pack_usage_path

    agent = ObservabilityAgent(
        telemetry=SkillsTelemetry(),
        scan=SkillsPhraseScan(),
        usage=SkillsObservabilityUsage(),
    )
    run_dir = str(tmp_path / "usage-route-run")
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    grok_home = str(tmp_path / "grok")
    sidecar = tmp_path / ".usage.json"
    monkeypatch.setattr(
        "observability.src.capabilities_skills_telemetry.pack_usage_path",
        lambda pack_root=None: sidecar,
    )

    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={
                "traces_action": "usage",
                "grok_home": grok_home,
                "run_dir": run_dir,
            },
        )
    )

    assert result.ok
    assert (Path(run_dir) / "usage.json").is_file()
    data = json.loads((Path(run_dir) / "usage.json").read_text())
    assert "items" in data
    assert "kept_sessions" in data


def test_agent_routes_phrases_to_build_phrases(tmp_path) -> None:
    """IT-OBS-003: Agent routes TRACES phrases action to build_phrases → writes phrase.json."""
    import json
    from pathlib import Path

    from observability.src.capabilities_observability_phrase import (
        SkillsObservabilityPhrase,
    )

    agent = ObservabilityAgent(
        scan=SkillsPhraseScan(),
        phrase=SkillsObservabilityPhrase(),
    )
    run_dir = str(tmp_path / "phrase-route-run")
    grok_home = str(tmp_path / "grok")
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    (Path(run_dir) / "sessions").mkdir(exist_ok=True)

    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={
                "traces_action": "phrases",
                "grok_home": grok_home,
                "run_dir": run_dir,
            },
        )
    )

    assert result.ok
    assert (Path(run_dir) / "phrase.json").is_file()
    data = json.loads((Path(run_dir) / "phrase.json").read_text())
    assert "exact_prompts" in data


def test_agent_routes_memory_to_scan_memory(tmp_path) -> None:
    """IT-OBS-004: Agent routes TRACES memory action to scan_memory → writes memory.json."""
    import json
    from pathlib import Path

    from observability.src.capabilities_observability_memory import (
        SkillsObservabilityMemory,
    )

    agent = ObservabilityAgent(
        memory=SkillsObservabilityMemory(),
    )
    run_dir = str(tmp_path / "memory-route-run")
    grok_home = str(tmp_path / "grok")
    Path(run_dir).mkdir(parents=True, exist_ok=True)

    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={
                "traces_action": "memory",
                "grok_home": grok_home,
                "run_dir": run_dir,
            },
        )
    )

    assert result.ok
    memory_path = Path(run_dir) / "memory.json"
    assert memory_path.is_file()
    data = json.loads(memory_path.read_text())
    assert data["source"] == "memory-v2"
    assert "topics" in data
    assert "observations" in data


def test_scan_memory_writes_memory_json_to_run_dir(tmp_path) -> None:
    """UT-OBSERVABILITY-004: scan_memory writes memory.json into run_dir."""
    from observability.src.capabilities_observability_memory import (
        SkillsObservabilityMemory,
    )

    memory = SkillsObservabilityMemory()
    run_dir = str(tmp_path / "memrun")
    grok_home = str(tmp_path / "grok")
    memory.scan_memory(
        grok_home,
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
