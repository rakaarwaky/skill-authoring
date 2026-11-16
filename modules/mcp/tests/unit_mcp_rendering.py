"""Unit tests: SkillsMcpAdapter multi-payload rendering.

Verifies that execute_tool() renders result.records (LIST, STATUS, USAGE)
and result.content (READ) instead of only result.message. Uses mock
aggregates to isolate from the real filesystem.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

_TOOLS_ROOT = Path(__file__).resolve().parents[2]
for _ns in (
    _TOOLS_ROOT,
    _TOOLS_ROOT / "shared" / "src",
    _TOOLS_ROOT / "mcp" / "src",
):
    if _ns.is_dir() and str(_ns) not in sys.path:
        sys.path.insert(0, str(_ns))

from shared.src.design.taxonomy_design_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
)
from shared.src.design.taxonomy_design_response import (
    SkillsExitCode,
    SkillsResult,
)
from shared.src.design.taxonomy_design_vo import TelemetryRow

from surface_mcp_command import SkillsMcpAdapter


# ─── Helpers ─────────────────────────────────────────────────────────

def _make_skill_record(name: str, description: str):
    """Create a minimal SkillRecord-like object for testing."""
    record = MagicMock()
    record.name = name
    record.description = description
    return record


def _make_telemetry_row(
    name: str,
    state: str = "active",
    pinned: bool = False,
    views: int = 0,
    uses: int = 0,
):
    """Create a real TelemetryRow for testing."""
    return TelemetryRow(
        name=name,
        state=state,
        pinned=pinned,
        created_by=None,
        created_at=None,
        first_seen_at=None,
        last_activity_at=None,
        archived_at=None,
        views=views,
        uses=uses,
        activity_window_start=None,
    )


def _make_mock_aggregate(result: SkillsResult):
    """Create a mock aggregate that always returns the given result."""
    agg = MagicMock()
    agg.execute.return_value = result
    return agg


# ─── Tests: execute_tool with LIST ───────────────────────────────────

def test_execute_tool_list_renders_two_column_table():
    """UT-MCP-RENDER-001: sac_list outputs a two-column SKILL/DESCRIPTION table."""
    records = (
        _make_skill_record("skill-a", "First skill description"),
        _make_skill_record("skill-b", "Second skill description"),
    )
    result = SkillsResult(ok=True, op=SkillsOp.LIST, records=records)
    adapter = SkillsMcpAdapter(_make_mock_aggregate(result))

    output = adapter.execute_tool("sac_list", {})
    text = output["content"][0]["text"]

    assert "SKILL" in text
    assert "DESCRIPTION" in text
    assert "skill-a" in text
    assert "skill-b" in text
    assert "First skill description" in text
    assert "Second skill description" in text
    assert "2 skills in the pack." in text
    assert output["ok"] is True


def test_execute_tool_list_empty_pack():
    """UT-MCP-RENDER-002: sac_list with no skills returns empty pack message."""
    result = SkillsResult(ok=True, op=SkillsOp.LIST, records=())
    adapter = SkillsMcpAdapter(_make_mock_aggregate(result))

    output = adapter.execute_tool("sac_list", {})
    text = output["content"][0]["text"]

    assert "No skills in the pack yet." in text
    assert output["ok"] is True


def test_execute_tool_list_truncates_long_description():
    """UT-MCP-RENDER-003: sac_list truncates descriptions over 70 chars."""
    long_desc = "A" * 80
    records = (_make_skill_record("long-skill", long_desc),)
    result = SkillsResult(ok=True, op=SkillsOp.LIST, records=records)
    adapter = SkillsMcpAdapter(_make_mock_aggregate(result))

    output = adapter.execute_tool("sac_list", {})
    text = output["content"][0]["text"]

    assert "…" in text
    assert "Tip: sac read <name> for full content" in text


# ─── Tests: execute_tool with READ ───────────────────────────────────

def test_execute_tool_read_returns_skill_content():
    """UT-MCP-RENDER-004: sac_read returns raw SKILL.md content."""
    content = "# My Skill\n\nThis is the skill body."
    result = SkillsResult(ok=True, op=SkillsOp.READ, content=content)
    adapter = SkillsMcpAdapter(_make_mock_aggregate(result))

    output = adapter.execute_tool("sac_read", {"skill": "arxiv"})
    text = output["content"][0]["text"]

    assert text == content
    assert output["ok"] is True


def test_execute_tool_read_skill_not_found():
    """UT-MCP-RENDER-005: sac_read with no content returns not-found message."""
    result = SkillsResult(
        ok=False,
        op=SkillsOp.READ,
        exit_code=SkillsExitCode.USAGE_ERROR,
        message="Skill not found: nonexistent",
    )
    adapter = SkillsMcpAdapter(_make_mock_aggregate(result))

    output = adapter.execute_tool("sac_read", {"skill": "nonexistent"})
    text = output["content"][0]["text"]

    assert "Skill not found" in text
    assert output["ok"] is False


# ─── Tests: execute_tool with STATUS ─────────────────────────────────

def test_execute_tool_status_renders_state_rows():
    """UT-MCP-RENDER-006: sac_status returns lifecycle state per skill."""
    records = (
        _make_telemetry_row("skill-a", state="active", pinned=False),
        _make_telemetry_row("skill-b", state="idle", pinned=True),
    )
    result = SkillsResult(ok=True, op=SkillsOp.STATUS, records=records)
    adapter = SkillsMcpAdapter(_make_mock_aggregate(result))

    output = adapter.execute_tool("sac_status", {})
    text = output["content"][0]["text"]

    assert "[OK] status — 2 state row(s)" in text
    assert "skill-a: active" in text
    assert "skill-b: idle (pinned)" in text
    assert output["ok"] is True


# ─── Tests: execute_tool with USAGE ──────────────────────────────────

def test_execute_tool_usage_renders_usage_rows():
    """UT-MCP-RENDER-007: sac_usage returns usage telemetry rows."""
    records = (
        _make_telemetry_row("skill-a", state="active", views=10, uses=5),
        _make_telemetry_row("skill-b", state="idle", views=3, uses=1),
    )
    result = SkillsResult(ok=True, op=SkillsOp.USAGE, records=records)
    adapter = SkillsMcpAdapter(_make_mock_aggregate(result))

    output = adapter.execute_tool("sac_usage", {})
    text = output["content"][0]["text"]

    assert "[OK] usage — 2 skill row(s)" in text
    assert "skill-a: views=10 uses=5 state=active" in text
    assert "skill-b: views=3 uses=1 state=idle" in text
    assert output["ok"] is True


# ─── Tests: execute_tool with unknown command ────────────────────────

def test_execute_tool_unknown_command_returns_error():
    """UT-MCP-RENDER-008: Unknown commands return structured error message."""
    result = SkillsResult(
        ok=False,
        op=SkillsOp.LIST,
        exit_code=SkillsExitCode.USAGE_ERROR,
        message="Unknown skills subcommand: bogus",
    )
    adapter = SkillsMcpAdapter(_make_mock_aggregate(result))

    output = adapter.execute_tool("sac_bogus", {})
    text = output["content"][0]["text"]

    assert "Unknown skills subcommand: bogus" in text
    assert output["ok"] is False


# ─── Tests: execute_tool with failure result ─────────────────────────

def test_execute_tool_failure_returns_error_message():
    """UT-MCP-RENDER-009: When result.ok is False, render message or exit fallback."""
    result = SkillsResult(
        ok=False,
        op=SkillsOp.LIST,
        exit_code=SkillsExitCode.ISSUES_FOUND,
        message="Some error occurred",
    )
    adapter = SkillsMcpAdapter(_make_mock_aggregate(result))

    output = adapter.execute_tool("sac_list", {})
    text = output["content"][0]["text"]

    assert text == "Some error occurred"
    assert output["ok"] is False


def test_execute_tool_failure_without_message_uses_exit_fallback():
    """UT-MCP-RENDER-010: When result.ok is False and no message, use exit fallback."""
    result = SkillsResult(
        ok=False,
        op=SkillsOp.LIST,
        exit_code=SkillsExitCode.ISSUES_FOUND,
        message="",
    )
    adapter = SkillsMcpAdapter(_make_mock_aggregate(result))

    output = adapter.execute_tool("sac_list", {})
    text = output["content"][0]["text"]

    assert "list: exit" in text
    assert output["ok"] is False