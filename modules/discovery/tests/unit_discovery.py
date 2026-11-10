"""Unit tests: BM25F ranker math and mock-based agent isolation for discovery.

Covers the ranker/tokenizer scoring math (UT-DISCOVERY-001..004) plus
mock-protocol agent tests that exercise SkillsDiscoveryAgent.execute and
show_skill in isolation from the filesystem (UT-DISCOVERY-005..014).
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

_TOOLS_ROOT = Path(__file__).resolve().parents[2]
for _ns in (
    _TOOLS_ROOT,
    _TOOLS_ROOT / "shared" / "src",
    _TOOLS_ROOT / "discovery" / "src",
):
    if _ns.is_dir() and str(_ns) not in sys.path:
        sys.path.insert(0, str(_ns))

from agent_discovery_orchestrator import SkillsDiscoveryAgent
from capabilities_discovery_catalog import SkillsCatalog
from capabilities_discovery_finder import SkillsDiscover
from shared.src.common.taxonomy_common_error import SkillsUsageError
from shared.src.common.taxonomy_common_vo import (
    DiscoveryResult,
    SkillContent,
    _Row,
)
from shared.src.discovery.contract_discovery_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
    ISkillsListerProtocol,
    ISkillsReaderProtocol,
)
from shared.src.discovery.taxonomy_discovery_request import (
    DiscoveryQuery,
    DiscoveryRequest,
    DiscoveryRoot,
    DiscoveryVerb,
)
from shared.src.discovery.taxonomy_discovery_vo import (
    BM25F_FIELD_WEIGHTS,
    SkillsBm25fRanker,
    build_index,
    tokenize,
)


def _row(skill: str, description: str, category: str = "automation") -> _Row:
    return _Row(
        skill=skill,
        category=category,
        description=description,
        path=f"{category}/{skill}",
        when_to_use="",
    )


def test_tokenize_lowercases_and_drops_short_words():
    """UT-DISCOVERY-001: tokenize lowercases and splits on whitespace."""
    tokens = tokenize("How do I list skills?")
    assert tokens == ["how", "do", "i", "list", "skills?"]


def test_ranker_ranks_relevant_skill_first():
    """UT-DISCOVERY-002: BM25F puts the most relevant skill on top."""
    ranker = SkillsBm25fRanker()
    rows = [
        _row("fetch-mcp", "Fetch web content via the MCP tool."),
        _row("backup", "Backup tar archives."),
    ]
    hits = ranker.rank(rows, tokenize("list fetch content"))
    assert len(hits) > 0
    assert hits[0].row.skill == "fetch-mcp"


def test_build_index_computes_field_stats():
    """UT-DISCOVERY-003: build_index precomputes field-level stats."""
    rows = [_row("a", "alpha beta"), _row("b", "alpha gamma")]
    index = build_index(rows)
    assert index.n_docs == 2
    assert index.avgdl["name"] >= 0.0


def test_field_weights_are_declared():
    """UT-DISCOVERY-004: name weighs heaviest in BM25F."""
    assert BM25F_FIELD_WEIGHTS["name"] == 5.0
    assert BM25F_FIELD_WEIGHTS["description"] == 3.0


def test_discover_empty_query_raises_usage_error():
    """UT-DISCOVERY-016: SkillsDiscover.discover raises SkillsUsageError on empty query."""
    catalog = SkillsCatalog()
    discover = SkillsDiscover(catalog, SkillsBm25fRanker())
    try:
        discover.discover(DiscoveryQuery(""), DiscoveryRoot(Path("/tmp/skills")), 20)
    except SkillsUsageError as exc:
        assert "Query is empty" in str(exc)
        assert exc.exit_code == 2
    else:
        raise AssertionError("Expected SkillsUsageError for empty query")


# ─── Mock-based unit tests: capability logic in isolation from the filesystem ─

def _agent_with(
    lister: ISkillsListerProtocol | None = None,
    reader: ISkillsReaderProtocol | None = None,
    catalog: ISkillsCatalogProtocol | None = None,
    discover: ISkillsDiscoverProtocol | None = None,
) -> SkillsDiscoveryAgent:
    """Build an agent from stubbed protocols; no real capabilities or FS used."""
    return SkillsDiscoveryAgent(
        catalog=catalog or MagicMock(spec=ISkillsCatalogProtocol),
        discover=discover or MagicMock(spec=ISkillsDiscoverProtocol),
        lister=lister or MagicMock(spec=ISkillsListerProtocol),
        reader=reader or MagicMock(spec=ISkillsReaderProtocol),
        default_root=DiscoveryRoot(Path("/tmp/skills")),
    )


def test_execute_discover_empty_query_usage_error():
    """UT-DISCOVERY-005: empty discover query returns exit_code 2 without touching FS."""
    agent = _agent_with()
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery(""),
            root=DiscoveryRoot(Path("/tmp/skills")),
        )
    )
    assert result.ok is False
    assert result.exit_code == 2
    assert result.discovery is None
    assert "Query required" in result.message


def test_execute_discover_whitespace_query_usage_error():
    """UT-DISCOVERY-009: whitespace-only discover query returns exit_code 2."""
    agent = _agent_with()
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("   "),
            root=DiscoveryRoot(Path("/tmp/skills")),
        )
    )
    assert result.ok is False
    assert result.exit_code == 2
    assert result.discovery is None
    assert "Query required" in result.message


def test_execute_discover_invalid_limit_usage_error():
    """UT-DISCOVERY-006: non-numeric limit returns exit_code 2, ValueError never escapes."""
    agent = _agent_with()
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("fetch"),
            root=DiscoveryRoot(Path("/tmp/skills")),
            flags={"limit": "abc"},
        )
    )
    assert result.ok is False
    assert result.exit_code == 2
    assert "Invalid limit" in result.message


def test_execute_discover_limit_zero_passes_through():
    """UT-DISCOVERY-010: limit "0" is a valid int and passes through."""
    discover = MagicMock(spec=ISkillsDiscoverProtocol)
    discover.discover.return_value = DiscoveryResult()
    agent = _agent_with(discover=discover)
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("fetch"),
            root=DiscoveryRoot(Path("/tmp/skills")),
            flags={"limit": "0"},
        )
    )
    assert result.ok is True
    _, _, limit = discover.discover.call_args[0]
    assert limit == 0


def test_execute_discover_limit_negative_passes_through():
    """UT-DISCOVERY-011: limit "-5" is a valid int and passes through."""
    discover = MagicMock(spec=ISkillsDiscoverProtocol)
    discover.discover.return_value = DiscoveryResult()
    agent = _agent_with(discover=discover)
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("fetch"),
            root=DiscoveryRoot(Path("/tmp/skills")),
            flags={"limit": "-5"},
        )
    )
    assert result.ok is True
    _, _, limit = discover.discover.call_args[0]
    assert limit == -5


def test_execute_discover_limit_empty_uses_default():
    """UT-DISCOVERY-012: empty-string limit falls back to the default 20."""
    discover = MagicMock(spec=ISkillsDiscoverProtocol)
    discover.discover.return_value = DiscoveryResult()
    agent = _agent_with(discover=discover)
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("fetch"),
            root=DiscoveryRoot(Path("/tmp/skills")),
            flags={"limit": ""},
        )
    )
    assert result.ok is True
    _, _, limit = discover.discover.call_args[0]
    assert limit == 20


def test_execute_discover_limit_large_passes_through():
    """UT-DISCOVERY-013: a large numeric limit passes through unchanged."""
    discover = MagicMock(spec=ISkillsDiscoverProtocol)
    discover.discover.return_value = DiscoveryResult()
    agent = _agent_with(discover=discover)
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("fetch"),
            root=DiscoveryRoot(Path("/tmp/skills")),
            flags={"limit": "1000000"},
        )
    )
    assert result.ok is True
    _, _, limit = discover.discover.call_args[0]
    assert limit == 1000000


def test_execute_discover_valid_limit_passes_through():
    """UT-DISCOVERY-007: a valid int limit passes through to the discover capability."""
    discover = MagicMock(spec=ISkillsDiscoverProtocol)
    discover.discover.return_value = DiscoveryResult()
    agent = _agent_with(discover=discover)
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("fetch"),
            root=DiscoveryRoot(Path("/tmp/skills")),
            flags={"limit": "3"},
        )
    )
    assert result.ok is True
    discover.discover.assert_called_once()
    _, _, limit = discover.discover.call_args[0]
    assert limit == 3


def test_execute_read_missing_query_exit_1():
    """UT-DISCOVERY-014: READ with missing query returns exit_code 1."""
    agent = _agent_with()
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.READ,
            query=DiscoveryQuery(""),
            root=DiscoveryRoot(Path("/tmp/skills")),
        )
    )
    assert result.ok is False
    assert result.exit_code == 1
    assert "Skill name required" in result.message


def test_execute_read_missing_skill_exit_1():
    """UT-DISCOVERY-015: READ with unresolvable skill returns exit_code 1."""
    reader = MagicMock(spec=ISkillsReaderProtocol)
    reader.show_skill.return_value = None
    agent = _agent_with(reader=reader)
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.READ,
            query=DiscoveryQuery("no-such-skill"),
            root=DiscoveryRoot(Path("/tmp/skills")),
        )
    )
    assert result.ok is False
    assert result.exit_code == 1
    assert "Skill not found" in result.message


def test_show_skill_routes_to_reader_without_filesystem():
    """UT-DISCOVERY-008: show_skill is a declared pass-through to the reader."""
    reader = MagicMock(spec=ISkillsReaderProtocol)
    reader.show_skill.return_value = SkillContent("---\nname: fetch\n---\n")
    agent = _agent_with(reader=reader)
    content = agent.show_skill("fetch", root=DiscoveryRoot(Path("/tmp/skills")))
    assert content == "---\nname: fetch\n---\n"
    reader.show_skill.assert_called_once_with(DiscoveryQuery("fetch"), DiscoveryRoot(Path("/tmp/skills")))


def test_show_skill_reader_returns_none_propagates_none():
    """UT-DISCOVERY-017: agent.show_skill propagates None when reader returns None."""
    reader = MagicMock(spec=ISkillsReaderProtocol)
    reader.show_skill.return_value = None
    agent = _agent_with(reader=reader)
    content = agent.show_skill("no-such-skill", root=DiscoveryRoot(Path("/tmp/skills")))
    assert content is None
    reader.show_skill.assert_called_once_with(DiscoveryQuery("no-such-skill"), DiscoveryRoot(Path("/tmp/skills")))
