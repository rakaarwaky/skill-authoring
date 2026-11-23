"""Observability-module unit test (AES704).

Verifies the agent's unknown-op handling and error propagation.
"""

from __future__ import annotations

from observability.src.agent_observability_orchestrator import (
    ObservabilityAgent,
)
from shared.src.design.taxonomy_design_request import SkillsRequest
from shared.src.design.taxonomy_design_response import SkillsExitCode


def test_unknown_op_returns_usage_error() -> None:
    agent = ObservabilityAgent()
    result = agent.execute(SkillsRequest(op="bogus", query=""))
    assert result.ok is False
    assert result.exit_code == SkillsExitCode.USAGE_ERROR


# ── Observability capability unit tests ─────────────────────────────────


def test_phrases_result_has_phrases_fields() -> None:
    """UT-OBSERVABILITY-001: SkillsResult carries phrases_exact/stems/lines."""
    from shared.src.design.taxonomy_design_request import SkillsOp
    from shared.src.design.taxonomy_design_response import SkillsResult

    r = SkillsResult(
        ok=True,
        op=SkillsOp.TRACES,
        phrases_exact=(("hello world", 2, 3, ("s1", "s2")),),
        phrases_stems=(),
        phrases_lines=(),
    )
    assert r.phrases_exact == (("hello world", 2, 3, ("s1", "s2")),)
    assert r.phrases_stems == ()
    assert r.phrases_lines == ()


def test_memory_report_roundtrips_via_skills_result() -> None:
    """UT-OBSERVABILITY-003: SkillsResult carries the memory report payload."""
    from shared.src.design.taxonomy_design_request import SkillsOp
    from shared.src.design.taxonomy_design_response import SkillsResult
    from shared.src.observability.taxonomy_observability_vo import (
        MemoryObservationRow,
        MemoryReport,
        MemoryTopicRow,
    )

    report = MemoryReport(
        topics=(
            MemoryTopicRow(
                workspace="global",
                title="orca worktree conventions",
                path="$HOME/.grok/memory-v2/global/topics/orca-worktree-conventions.md",
                skill_names=("skill-traces", "skill-authoring"),
                quoted_lines=("skill-traces reads memory topics",),
                matched_section="learn",
            ),
        ),
        observations=(
            MemoryObservationRow(
                type="stale",
                quoted="skill-improve step-5-verifiy does not exist",
                workspace="skill-authoring-cdc4148d",
            ),
        ),
        keep_list=("skill-traces",),
    )

    r = SkillsResult(
        ok=True,
        op=SkillsOp.TRACES,
        memory=report,
    )
    assert r.memory is report
    assert r.memory.topics[0].skill_names == ("skill-traces", "skill-authoring")
    assert r.memory.observations[0].type == "stale"
    assert r.memory.keep_list == ("skill-traces",)


def test_execute_tool_empty_message_fallback() -> None:
    """UT-OBSERVABILITY-002: MCP execute_tool returns a meaningful fallback string."""
    from mcp.src.surface_mcp_command import SkillsMcpAdapter
    from shared.src.design.taxonomy_design_request import SkillsOp
    from shared.src.design.taxonomy_design_response import SkillsResult

    class FakeAggregate:
        def execute(self, request):
            return SkillsResult(ok=True, op=SkillsOp.LIST, exit_code=0, message="")

    adapter = SkillsMcpAdapter(FakeAggregate())
    out = adapter.execute_tool("sac_list", {})
    assert out["content"][0]["text"] == "No skills in the pack yet."


# ── clear_run_dir per-action scoping (shared utility) ─────────────────────


def test_clear_run_dir_usage_preserves_phrase_json(tmp_path) -> None:
    """UT-OBS-005: clear_run_dir('usage') wipes usage.json only, preserves phrase.json."""
    import json

    from shared.src.observability.utility_observability_run_dir import clear_run_dir

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "sessions").mkdir()
    (run_dir / "sessions" / "0001-s.json").write_text("{}")
    (run_dir / "manifest.json").write_text("{}")
    (run_dir / "phrase.json").write_text("{}")
    (run_dir / "usage.json").write_text("{}")
    (run_dir / "memory.json").write_text("{}")

    clear_run_dir(str(run_dir), action="usage")

    # sessions/ and manifest.json are owned by scan_sessions, not clear_run_dir.
    assert (run_dir / "sessions").exists()
    assert (run_dir / "manifest.json").exists()
    assert not (run_dir / "usage.json").exists()
    assert (run_dir / "phrase.json").exists()
    assert json.loads((run_dir / "phrase.json").read_text()) == {}
    # memory.json must survive a usage clear.
    assert (run_dir / "memory.json").exists()
    assert json.loads((run_dir / "memory.json").read_text()) == {}


def test_clear_run_dir_phrase_preserves_usage_json(tmp_path) -> None:
    """UT-OBS-006: clear_run_dir('phrase') wipes phrase.json only, preserves usage.json."""
    from shared.src.observability.utility_observability_run_dir import clear_run_dir

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "sessions").mkdir()
    (run_dir / "sessions" / "0001-s.json").write_text("{}")
    (run_dir / "manifest.json").write_text("{}")
    (run_dir / "phrase.json").write_text("{}")
    (run_dir / "usage.json").write_text("{}")
    (run_dir / "memory.json").write_text("{}")

    clear_run_dir(str(run_dir), action="phrase")

    # sessions/ and manifest.json are owned by scan_sessions, not clear_run_dir.
    assert (run_dir / "sessions").exists()
    assert (run_dir / "manifest.json").exists()
    assert not (run_dir / "phrase.json").exists()
    assert (run_dir / "usage.json").exists()
    # memory.json must survive a phrase clear.
    assert (run_dir / "memory.json").exists()


def test_clear_run_dir_memory_only_clears_memory_json(tmp_path) -> None:
    """UT-OBS-007: clear_run_dir('memory') only wipes memory.json."""
    from shared.src.observability.utility_observability_run_dir import clear_run_dir

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "memory.json").write_text("{}")
    (run_dir / "phrase.json").write_text("{}")
    (run_dir / "usage.json").write_text("{}")
    (run_dir / "manifest.json").write_text("{}")

    clear_run_dir(str(run_dir), action="memory")

    assert not (run_dir / "memory.json").exists()
    assert (run_dir / "phrase.json").exists()
    assert (run_dir / "usage.json").exists()
    assert (run_dir / "manifest.json").exists()


# ── New capability artifact tests ─────────────────────────────────────────


def test_build_phrases_writes_phrase_json(tmp_path) -> None:
    """UT-OBS-012: SkillsObservabilityPhrase.build_phrases writes phrase.json to run_dir."""
    import json
    from pathlib import Path

    from observability.src.capabilities_observability_phrase import (
        SkillsObservabilityPhrase,
    )

    phrase = SkillsObservabilityPhrase()
    run_dir = str(tmp_path / "phrase-run")
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    (Path(run_dir) / "sessions").mkdir(exist_ok=True)

    phrase.build_phrases("$HOME/.grok", run_dir)

    assert (Path(run_dir) / "phrase.json").is_file()
    data = json.loads((Path(run_dir) / "phrase.json").read_text())
    assert "exact_prompts" in data
    assert "prompt_stems_12_words" in data
    assert "repeated_instruction_lines" in data


def test_write_usage_writes_usage_json(tmp_path) -> None:
    """UT-OBS-013: SkillsObservabilityUsage.write_usage writes usage.json to run_dir."""
    import json
    from pathlib import Path

    from observability.src.capabilities_observability_usage import (
        SkillsObservabilityUsage,
    )
    from shared.src.observability.taxonomy_observability_entity import (
        TraceSessionRecord,
    )

    usage = SkillsObservabilityUsage()
    run_dir = str(tmp_path / "usage-run")
    Path(run_dir).mkdir(parents=True, exist_ok=True)

    records: tuple[TraceSessionRecord, ...] = ()
    usage.write_usage("$HOME/.grok", run_dir, records)

    assert (Path(run_dir) / "usage.json").is_file()
    data = json.loads((Path(run_dir) / "usage.json").read_text())
    assert "items" in data
    assert "kept_sessions" in data


def test_scan_memory_writes_memory_json(tmp_path) -> None:
    """UT-OBS-014: SkillsObservabilityMemory.scan_memory writes memory.json to run_dir."""
    import json
    from pathlib import Path

    from observability.src.capabilities_observability_memory import (
        SkillsObservabilityMemory,
    )

    memory = SkillsObservabilityMemory()
    run_dir = str(tmp_path / "mem-run")
    Path(run_dir).mkdir(parents=True, exist_ok=True)

    memory.scan_memory("$HOME/.grok", run_dir)

    assert (Path(run_dir) / "memory.json").is_file()
    data = json.loads((Path(run_dir) / "memory.json").read_text())
    assert data["source"] == "memory-v2"
    assert "topics" in data
    assert "observations" in data
    assert "keep_list" in data


# ── Agent-to-capability routing tests ─────────────────────────────────────


def test_execute_phrases_calls_phrase_build_phrases(tmp_path) -> None:
    """UT-OBS-015: _execute_phrases calls self._phrase.build_phrases."""
    from observability.src.agent_observability_orchestrator import ObservabilityAgent
    from shared.src.design.taxonomy_design_request import SkillsOp, SkillsRequest
    from shared.src.observability.taxonomy_observability_entity import ScanResult
    from shared.src.observability.taxonomy_observability_vo import PhrasesReport

    calls = []

    class FakePhrase:
        def build_phrases(self, grok_home, run_dir):
            calls.append((grok_home, run_dir))
            return PhrasesReport()

    class FakeScan:
        def scan_sessions(self, grok_home, run_dir):
            return ScanResult(records=(), sessions_seen=0)

    agent = ObservabilityAgent(scan=FakeScan(), phrase=FakePhrase())
    run_dir = str(tmp_path / "run")
    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={
                "traces_action": "phrases",
                "grok_home": "$HOME/.grok",
                "run_dir": run_dir,
            },
        )
    )

    assert result.ok
    assert calls == [("$HOME/.grok", run_dir)]


def test_execute_usage_traces_calls_usage_and_telemetry(tmp_path) -> None:
    """UT-OBS-016: _execute_usage_traces calls write_usage + fold_used_count_into_sidecar."""
    from observability.src.agent_observability_orchestrator import ObservabilityAgent
    from shared.src.design.taxonomy_design_request import SkillsOp, SkillsRequest
    from shared.src.observability.taxonomy_observability_entity import ScanResult

    usage_calls = []
    fold_calls = []

    class FakeUsage:
        def write_usage(self, grok_home, run_dir, records):
            usage_calls.append((grok_home, run_dir, records))
            return []

        def fold_used_count_into_sidecar(self, grok_home, run_dir, records):
            fold_calls.append((grok_home, run_dir, records))

    class FakeScan:
        def scan_sessions(self, grok_home, run_dir):
            return ScanResult(records=(), sessions_seen=0)

    agent = ObservabilityAgent(scan=FakeScan(), usage=FakeUsage())
    run_dir = str(tmp_path / "run")
    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={
                "traces_action": "usage",
                "grok_home": "$HOME/.grok",
                "run_dir": run_dir,
            },
        )
    )

    assert result.ok
    assert usage_calls == [("$HOME/.grok", run_dir, ())]
    assert fold_calls == [("$HOME/.grok", run_dir, ())]


def test_execute_memory_calls_memory_scan_memory(tmp_path) -> None:
    """UT-OBS-017: _execute_memory calls self._memory.scan_memory."""
    from observability.src.agent_observability_orchestrator import ObservabilityAgent
    from shared.src.design.taxonomy_design_request import SkillsOp, SkillsRequest
    from shared.src.observability.taxonomy_observability_vo import MemoryReport

    memory_calls = []

    class FakeMemory:
        def scan_memory(self, grok_home, run_dir):
            memory_calls.append((grok_home, run_dir))
            return MemoryReport()

    agent = ObservabilityAgent(memory=FakeMemory())
    run_dir = str(tmp_path / "run")
    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={
                "traces_action": "memory",
                "grok_home": "$HOME/.grok",
                "run_dir": run_dir,
            },
        )
    )

    assert result.ok
    assert memory_calls == [("$HOME/.grok", run_dir)]


# ── SkillsObservabilityUsage.fold_used_count_into_sidecar analytics seeding ─────────


def test_fold_used_count_into_sidecar_seeds_analytics(tmp_path, monkeypatch) -> None:
    """UT-OBS-008: SkillsObservabilityUsage.fold_used_count_into_sidecar writes sessions/last_used/via fields."""
    import json

    from observability.src.capabilities_observability_usage import (
        SkillsObservabilityUsage,
    )

    sidecar = tmp_path / ".usage.json"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(json.dumps({
        "my-skill": {
            "state": "active",
            "pinned": False,
        }
    }))
    monkeypatch.setattr(
        "observability.src.capabilities_observability_usage.pack_usage_path",
        lambda pack_root=None: sidecar,
    )
    usage_dir = tmp_path / "run"
    usage_dir.mkdir()
    (usage_dir / "usage.json").write_text(json.dumps({
        "items": [
            {
                "kind": "skill",
                "name": "my-skill",
                "used_count": 5,
                "sessions": ["s1", "s2"],
                "last_used": "2026-11-20T10:00:00+00:00",
                "via": {"skill_file_read": 3, "slash": 2},
            }
        ]
    }))

    usage = SkillsObservabilityUsage()
    usage.fold_used_count_into_sidecar(str(tmp_path), str(usage_dir), ())

    written = json.loads(sidecar.read_text())
    rec = written["my-skill"]
    assert rec["used_count"] == 5
    assert rec["sessions"] == ["s1", "s2"]
    assert rec["last_used"] == "2026-11-20T10:00:00+00:00"
    assert rec["via"] == {"skill_file_read": 3, "slash": 2}
    # Lifecycle fields preserved.
    assert rec["state"] == "active"
    assert rec["pinned"] is False


def test_seed_record_if_missing_creates_baseline(tmp_path, monkeypatch) -> None:
    """UT-OBS-018: seed_record_if_missing creates a baseline record if skill not present."""
    import json

    from observability.src.capabilities_observability_usage import (
        SkillsObservabilityUsage,
    )

    sidecar = tmp_path / ".usage.json"
    sidecar.write_text(json.dumps({"existing-skill": {"state": "active"}}))
    monkeypatch.setattr(
        "observability.src.capabilities_observability_usage.pack_usage_path",
        lambda pack_root=None: sidecar,
    )

    usage = SkillsObservabilityUsage()
    usage.seed_record_if_missing("new-skill", str(tmp_path))

    data = json.loads(sidecar.read_text())
    assert "new-skill" in data
    assert data["new-skill"]["state"] == "active"
    assert data["new-skill"]["used_count"] == 0
    assert data["existing-skill"] == {"state": "active"}

    # Calling again does not overwrite existing record
    data["new-skill"]["used_count"] = 42
    sidecar.write_text(json.dumps(data))
    usage.seed_record_if_missing("new-skill", str(tmp_path))
    data2 = json.loads(sidecar.read_text())
    assert data2["new-skill"]["used_count"] == 42


def test_reanchor_clock_updates_timestamps(tmp_path, monkeypatch) -> None:
    """UT-OBS-019: reanchor_clock updates last_activity_at and activity_window_start."""
    import json

    from observability.src.capabilities_observability_usage import (
        SkillsObservabilityUsage,
    )

    sidecar = tmp_path / ".usage.json"
    sidecar.write_text(json.dumps({
        "my-skill": {
            "state": "active",
            "last_activity_at": "2026-01-01T00:00:00+00:00",
            "activity_window_start": "2026-01-01T00:00:00+00:00",
        }
    }))
    monkeypatch.setattr(
        "observability.src.capabilities_observability_usage.pack_usage_path",
        lambda pack_root=None: sidecar,
    )

    usage = SkillsObservabilityUsage()
    usage.reanchor_clock("my-skill", str(tmp_path))

    data = json.loads(sidecar.read_text())
    assert data["my-skill"]["last_activity_at"] > "2026-01-01T00:00:00+00:00"
    assert data["my-skill"]["activity_window_start"] > "2026-01-01T00:00:00+00:00"


def test_curated_report_returns_rows(tmp_path, monkeypatch) -> None:
    """UT-OBS-020: curated_report returns sorted TelemetryRow objects for pack skills."""
    import json

    from observability.src.capabilities_observability_usage import (
        SkillsObservabilityUsage,
    )

    # Create skill folders with SKILL.md under tmp_path
    skill_a_dir = tmp_path / "general" / "skill-a"
    skill_a_dir.mkdir(parents=True)
    (skill_a_dir / "SKILL.md").write_text("---\nname: skill-a\n---\n")

    skill_b_dir = tmp_path / "general" / "skill-b"
    skill_b_dir.mkdir(parents=True)
    (skill_b_dir / "SKILL.md").write_text("---\nname: skill-b\n---\n")

    sidecar = tmp_path / ".usage.json"
    sidecar.write_text(json.dumps({
        "skill-a": {
            "state": "active",
            "pinned": True,
            "used_count": 10,
        }
    }))
    monkeypatch.setattr(
        "observability.src.capabilities_observability_usage.pack_usage_path",
        lambda pack_root=None: sidecar,
    )

    usage = SkillsObservabilityUsage()
    rows = usage.curated_report(str(tmp_path))

    assert len(rows) == 2
    row_a = next(r for r in rows if r.name == "skill-a")
    row_b = next(r for r in rows if r.name == "skill-b")
    assert row_a.name == "skill-a"
    assert row_a.pinned is True
    assert row_a.used_count == 10
    assert row_b.name == "skill-b"
    assert row_b.pinned is False
    assert row_b.used_count == 0


def test_record_use_bumps_used_count(tmp_path, monkeypatch) -> None:
    """UT-OBS-021: record_use increments used_count in .usage.json."""
    import json

    from observability.src.capabilities_observability_usage import (
        SkillsObservabilityUsage,
    )

    sidecar = tmp_path / ".usage.json"
    sidecar.write_text(json.dumps({
        "my-skill": {
            "state": "active",
            "used_count": 3,
        }
    }))
    monkeypatch.setattr(
        "observability.src.capabilities_observability_usage.pack_usage_path",
        lambda pack_root=None: sidecar,
    )

    usage = SkillsObservabilityUsage()
    usage.record_use("my-skill", str(tmp_path))

    data = json.loads(sidecar.read_text())
    assert data["my-skill"]["used_count"] == 4
    assert data["my-skill"]["last_activity_at"] is not None
    assert data["my-skill"]["state"] == "active"
    assert data["my-skill"]["pinned"] is False


# ── scan_sessions with action="usage" writes usage.json not phrase.json ──

def test_scan_sessions_usage_action_writes_usage_not_phrases(tmp_path) -> None:
    """UT-OBS-009: scan_sessions + write_usage writes usage.json, not phrase.json."""
    from pathlib import Path

    from observability.src.capabilities_observability_usage import (
        SkillsObservabilityUsage,
    )
    from observability.src.capabilities_skills_phrase_scan import SkillsPhraseScan

    scan = SkillsPhraseScan()
    usage = SkillsObservabilityUsage()
    run_dir = str(tmp_path / "run")
    # Empty grok_home — no sessions, but scan_sessions should still work.
    scan_result = scan.scan_sessions(str(tmp_path / "grok"), run_dir)
    usage.write_usage("$HOME/.grok", run_dir, scan_result.records)

    assert (Path(run_dir) / "usage.json").is_file()
    assert not (Path(run_dir) / "phrase.json").exists()


# ── _baseline_record() defaults ─────────────────────────────────────────────


def test_baseline_record_defaults() -> None:
    """UT-OBS-010: _baseline_record() returns the canonical default fields."""
    from shared.src.maintenance.utility_lifecycle_support import _baseline_record

    rec = _baseline_record()
    assert rec["state"] == "active"
    assert rec["pinned"] is False
    assert isinstance(rec["created_by"], str) and rec["created_by"]
    assert isinstance(rec["created_at"], str) and rec["created_at"]
    assert rec["first_seen_at"] == rec["created_at"]
    assert rec["last_activity_at"] == rec["created_at"]
    assert rec["archived_at"] == ""
    assert rec["used_count"] == 0
    assert isinstance(rec["activity_window_start"], str) and rec["activity_window_start"]
    assert rec["sessions"] == []
    assert rec["last_used"] is None
    assert rec["via"] == {}


def test_normalize_preserves_baseline_defaults() -> None:
    """UT-OBS-011: _normalize() keeps missing fields at baseline defaults."""
    from shared.src.maintenance.utility_lifecycle_support import (
        _baseline_record,
        _normalize,
    )

    baseline = _baseline_record()
    rec = _normalize({"name": "only-name-provided"})
    # All baseline defaults are preserved.
    assert rec["state"] == baseline["state"]
    assert rec["pinned"] == baseline["pinned"]
    assert rec["created_by"] == baseline["created_by"]
    assert rec["used_count"] == baseline["used_count"]
    assert rec["sessions"] == []
    assert rec["last_used"] is None
    assert rec["via"] == {}
