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
    assert out["content"][0]["text"] == "list: exit 0"
