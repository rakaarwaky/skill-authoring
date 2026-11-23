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


# ── _clear_run_dir per-action scoping ─────────────────────────────────────

def test_clear_run_dir_usage_preserves_phrases_json(tmp_path) -> None:
    """UT-OBS-005: _clear_run_dir('usage') wipes sessions/manifest/usage.json only."""
    import json

    from observability.src.capabilities_skills_phrase_scan import _clear_run_dir

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "sessions").mkdir()
    (run_dir / "sessions" / "0001-s.json").write_text("{}")
    (run_dir / "manifest.json").write_text("{}")
    (run_dir / "phrases.json").write_text("{}")
    (run_dir / "usage.json").write_text("{}")

    _clear_run_dir(str(run_dir), action="usage")

    assert not (run_dir / "sessions").exists()
    assert not (run_dir / "manifest.json").exists()
    assert not (run_dir / "usage.json").exists()
    assert (run_dir / "phrases.json").exists()
    assert json.loads((run_dir / "phrases.json").read_text()) == {}


def test_clear_run_dir_phrases_preserves_usage_json(tmp_path) -> None:
    """UT-OBS-006: _clear_run_dir('phrases') wipes sessions/manifest/phrases.json only."""
    from observability.src.capabilities_skills_phrase_scan import _clear_run_dir

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "sessions").mkdir()
    (run_dir / "sessions" / "0001-s.json").write_text("{}")
    (run_dir / "manifest.json").write_text("{}")
    (run_dir / "phrases.json").write_text("{}")
    (run_dir / "usage.json").write_text("{}")

    _clear_run_dir(str(run_dir), action="phrases")

    assert not (run_dir / "sessions").exists()
    assert not (run_dir / "manifest.json").exists()
    assert not (run_dir / "phrases.json").exists()
    assert (run_dir / "usage.json").exists()


def test_clear_run_dir_memory_only_clears_memory_json(tmp_path) -> None:
    """UT-OBS-007: _clear_run_dir('memory') only wipes memory.json."""
    from observability.src.capabilities_skills_phrase_scan import _clear_run_dir

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "memory.json").write_text("{}")
    (run_dir / "phrases.json").write_text("{}")
    (run_dir / "usage.json").write_text("{}")
    (run_dir / "manifest.json").write_text("{}")

    _clear_run_dir(str(run_dir), action="memory")

    assert not (run_dir / "memory.json").exists()
    assert (run_dir / "phrases.json").exists()
    assert (run_dir / "usage.json").exists()
    assert (run_dir / "manifest.json").exists()


# ── _fold_used_count_into_sidecar analytics seeding ───────────────────────

def test_fold_used_count_into_sidecar_seeds_analytics(tmp_path) -> None:
    """UT-OBS-008: _fold_used_count_into_sidecar writes sessions/last_used/via fields."""
    import json

    from observability.src.capabilities_skills_phrase_scan import (
        _fold_used_count_into_sidecar,
    )

    sidecar = tmp_path / ".usage.json"
    sidecar_data = {
        "my-skill": {
            "state": "active",
            "pinned": False,
        }
    }
    items = [
        {
            "kind": "skill",
            "name": "my-skill",
            "used_count": 5,
            "sessions": ["s1", "s2"],
            "last_used": "2026-11-20T10:00:00+00:00",
            "via": {"skill_file_read": 3, "slash": 2},
        }
    ]
    _fold_used_count_into_sidecar(str(sidecar), sidecar_data, items)
    written = json.loads(sidecar.read_text())
    rec = written["my-skill"]
    assert rec["used_count"] == 5
    assert rec["sessions"] == ["s1", "s2"]
    assert rec["last_used"] == "2026-11-20T10:00:00+00:00"
    assert rec["via"] == {"skill_file_read": 3, "slash": 2}
    # Lifecycle fields preserved.
    assert rec["state"] == "active"
    assert rec["pinned"] is False


# ── scan_sessions with action="usage" writes usage.json not phrases.json ──

def test_scan_sessions_usage_action_writes_usage_not_phrases(tmp_path) -> None:
    """UT-OBS-009: scan_sessions(action='usage') writes usage.json, not phrases.json."""
    from pathlib import Path

    from observability.src.capabilities_skills_phrase_scan import SkillsPhraseScan

    scan = SkillsPhraseScan()
    run_dir = str(tmp_path / "run")
    # Empty grok_home — no sessions, but scan_sessions should still work.
    scan.scan_sessions(str(tmp_path / "grok"), run_dir, action="usage")
    assert (Path(run_dir) / "usage.json").is_file()
    assert not (Path(run_dir) / "phrases.json").exists()
