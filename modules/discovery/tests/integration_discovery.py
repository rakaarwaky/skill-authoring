"""Integration tests: DI wiring of the discovery agent over real pack trees."""
from __future__ import annotations

import sys
from pathlib import Path

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
from capabilities_discovery_lister import SkillsLister
from capabilities_discovery_reader import SkillsPackReader

from shared.src.discovery.taxonomy_discovery_request import (
    DiscoveryQuery,
    DiscoveryRequest,
    DiscoveryRoot,
    DiscoveryVerb,
)
from shared.src.discovery.taxonomy_discovery_vo import SkillsBm25fRanker


def _make_agent(root: Path) -> SkillsDiscoveryAgent:
    catalog = SkillsCatalog()
    discover = SkillsDiscover(catalog, SkillsBm25fRanker())
    lister = SkillsLister(root)
    reader = SkillsPackReader(root)
    return SkillsDiscoveryAgent(
        catalog=catalog, discover=discover, lister=lister, reader=reader,
    )


def test_list_routes_to_lister(tmp_path):
    """INT-DISCOVERY-001: LIST op resolves through the injected lister."""
    skill = tmp_path / "automation" / "fetch" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: fetch\ndescription: Fetch web content.\n---\n# Fetch\n",
        encoding="utf-8",
    )
    agent = _make_agent(tmp_path)
    result = agent.execute(
        DiscoveryRequest(verb=DiscoveryVerb.LIST, root=DiscoveryRoot(tmp_path))
    )
    assert result.ok is True
    assert len(result.records) == 1
    assert result.records[0].name == "fetch"


def test_read_routes_to_reader(tmp_path):
    """INT-DISCOVERY-002: READ op resolves one skill through the reader."""
    skill = tmp_path / "automation" / "fetch" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: fetch\ndescription: Fetch web content.\n---\n# Fetch\n",
        encoding="utf-8",
    )
    agent = _make_agent(tmp_path)
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.READ,
            query=DiscoveryQuery("fetch"),
            root=DiscoveryRoot(tmp_path),
        )
    )
    assert result.ok is True
    assert "Fetch web content" in str(result.content)


def test_list_skills_json_source_names_walked_root(tmp_path):
    """INT-DISCOVERY-003: list_skills_json source names the actually-walked root."""
    skill = tmp_path / "automation" / "fetch" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: fetch\ndescription: Fetch web content.\n---\n# Fetch\n",
        encoding="utf-8",
    )
    other = tmp_path / "other"
    (other / "automation" / "fetch").mkdir(parents=True)
    (other / "automation" / "fetch" / "SKILL.md").write_text(
        "---\nname: fetch\ndescription: Fetch web content.\n---\n# Fetch\n",
        encoding="utf-8",
    )
    lister = SkillsLister(tmp_path)
    payload = lister.list_skills_json(root=DiscoveryRoot(other))
    assert payload["skills"][0]["source"] == str(other)
    # No override: source equals the construction root.
    payload_default = lister.list_skills_json()
    assert payload_default["skills"][0]["source"] == str(tmp_path)


def test_show_skill_ambiguous_exact_match_returns_none(tmp_path):
    """INT-DISCOVERY-004: two skills sharing a frontmatter name resolve to None."""
    for cat in ("automation", "office"):
        skill_dir = tmp_path / cat / "fetch"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: fetch\ndescription: A fetch skill.\n---\n# Fetch\n",
            encoding="utf-8",
        )
    reader = SkillsPackReader(tmp_path)
    assert reader.show_skill(DiscoveryQuery("fetch"), root=DiscoveryRoot(tmp_path)) is None


def test_read_ambiguous_exact_match_agent_exit_1(tmp_path):
    """INT-DISCOVERY-005: two skills sharing a frontmatter name -> agent READ exit 1."""
    for cat in ("automation", "office"):
        skill_dir = tmp_path / cat / "fetch"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: fetch\ndescription: A fetch skill.\n---\n# Fetch\n",
            encoding="utf-8",
        )
    agent = _make_agent(tmp_path)
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.READ,
            query=DiscoveryQuery("fetch"),
            root=DiscoveryRoot(tmp_path),
        )
    )
    assert result.ok is False
    assert result.exit_code == 1
    assert "Skill not found" in result.message


def test_read_skill_named_none_is_resolvable(tmp_path):
    """INT-DISCOVERY-006: a skill literally named None is readable after dropping the 'None' guard."""
    skill_dir = tmp_path / "automation" / "None"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: None\ndescription: A skill literally named None.\n---\n# None\n",
        encoding="utf-8",
    )
    agent = _make_agent(tmp_path)
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.READ,
            query=DiscoveryQuery("None"),
            root=DiscoveryRoot(tmp_path),
        )
    )
    assert result.ok is True
    assert result.content is not None
    assert "A skill literally named None" in str(result.content)


def test_show_skill_single_prefix_match_returns_content(tmp_path):
    """INT-DISCOVERY-007: single prefixed candidate (fetch-mcp) resolves for query 'fetch'."""
    skill_dir = tmp_path / "automation" / "fetch-mcp"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: fetch-mcp\ndescription: Fetch web pages.\n---\n# Fetch MCP\n",
        encoding="utf-8",
    )
    reader = SkillsPackReader(tmp_path)
    content = reader.show_skill(
        DiscoveryQuery("fetch"), root=DiscoveryRoot(tmp_path)
    )
    assert content is not None
    assert "Fetch web pages" in str(content)


def test_show_skill_ambiguous_prefix_match_returns_none(tmp_path):
    """INT-DISCOVERY-009: multiple prefixed candidates (fetch-mcp, fetch-cli) -> None (FR-discovery-002)."""
    for name in ("fetch-mcp", "fetch-cli"):
        skill_dir = tmp_path / "automation" / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Fetch {name}.\n---\n# {name}\n",
            encoding="utf-8",
        )
    reader = SkillsPackReader(tmp_path)
    assert reader.show_skill(DiscoveryQuery("fetch"), root=DiscoveryRoot(tmp_path)) is None


def test_list_skills_root_override(tmp_path):
    """INT-DISCOVERY-010: list_skills(root=...) returns records from the override root (FR-discovery-001)."""
    skill_dir = tmp_path / "other" / "automation" / "fetch"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: fetch\ndescription: Fetch web content.\n---\n# Fetch\n",
        encoding="utf-8",
    )
    lister = SkillsLister(tmp_path)
    records = lister.list_skills(root=DiscoveryRoot(tmp_path / "other"))
    assert len(records) == 1
    assert records[0].name == "fetch"
    assert records[0].path == tmp_path / "other" / "automation" / "fetch" / "SKILL.md"
def test_list_skills_empty_pack(tmp_path):
    """INT-DISCOVERY-008: empty pack returns empty record sequence."""
    lister = SkillsLister(tmp_path)
    assert lister.list_skills() == ()
    payload = lister.list_skills_json()
    assert payload == {"skills": []}


def test_discover_empty_query_exit_2(tmp_path):
    """INT-DISCOVERY-011: agent-level empty discover query -> exit 2 end-to-end (FR-discovery-004/INT)."""
    agent = _make_agent(tmp_path)
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery(""),
            root=DiscoveryRoot(tmp_path),
        )
    )
    assert result.ok is False
    assert result.exit_code == 2
    assert "Query required" in result.message
