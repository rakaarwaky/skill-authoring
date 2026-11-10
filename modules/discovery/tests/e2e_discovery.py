"""E2E tests: full request lifecycle over a real skills tree."""
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


def _seed_skills(tmp_path: Path) -> None:
    skills = {
        "automation/fetch-mcp": ("fetch", "Fetch web pages and scrape to markdown."),
        "office/docx": ("docx", "Create and edit Word docx files."),
        "research-study/arxiv": ("arxiv", "Search arXiv papers by keyword or id."),
    }
    for cat_name, (skill_name, desc) in skills.items():
        cat, name = cat_name.split("/")
        skill_dir = tmp_path / cat / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {skill_name}\ndescription: {desc}\n"
            f"when-to-use: Use when {desc.lower()}\n---\n# {name.title()}\n",
            encoding="utf-8",
        )


def test_catalog_then_discover_round_trip(tmp_path):
    """E2E-DISCOVERY-001: catalog rebuild -> discover returns ranked hits."""
    _seed_skills(tmp_path)
    catalog = SkillsCatalog()
    agent = SkillsDiscoveryAgent(
        catalog=catalog,
        discover=SkillsDiscover(catalog, SkillsBm25fRanker()),
        lister=SkillsLister(tmp_path),
        reader=SkillsPackReader(tmp_path),
    )
    rebuild = agent.execute(DiscoveryRequest(verb=DiscoveryVerb.CATALOG, root=DiscoveryRoot(tmp_path)))
    assert rebuild.ok is True
    search = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("arxiv papers"),
            root=DiscoveryRoot(tmp_path),
        )
    )
    assert search.ok is True
    assert search.discovery is not None
    assert len(search.discovery.matches) > 0
    assert search.discovery.matches[0].skill == "arxiv"


def test_discover_fallback_on_corrupt_catalog(tmp_path):
    """E2E-DISCOVERY-002: corrupt catalog.json -> tree scan fallback with warnings."""
    _seed_skills(tmp_path)
    catalog = SkillsCatalog()
    agent = SkillsDiscoveryAgent(
        catalog=catalog,
        discover=SkillsDiscover(catalog, SkillsBm25fRanker()),
        lister=SkillsLister(tmp_path),
        reader=SkillsPackReader(tmp_path),
    )

    # Write a corrupt catalog.json so discover must fall back to the live tree scan.
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text("{ not valid json ", encoding="utf-8")

    search = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("arxiv papers"),
            root=DiscoveryRoot(tmp_path),
        )
    )
    assert search.ok is True
    assert search.discovery is not None
    # Matches come from the live tree scan, not the corrupt catalog.
    assert len(search.discovery.matches) > 0
    assert any(m.skill == "arxiv" for m in search.discovery.matches)
    # Warning fields are set to report the drift.
    assert search.discovery.warning
    assert search.discovery.warning_detail


def test_discover_fallback_on_missing_catalog(tmp_path):
    """E2E-DISCOVERY-003: no catalog.json -> tree scan fallback with warnings."""
    _seed_skills(tmp_path)
    catalog = SkillsCatalog()
    agent = SkillsDiscoveryAgent(
        catalog=catalog,
        discover=SkillsDiscover(catalog, SkillsBm25fRanker()),
        lister=SkillsLister(tmp_path),
        reader=SkillsPackReader(tmp_path),
    )

    # Never write catalog.json; discover must fall back to the live tree scan.
    search = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("arxiv papers"),
            root=DiscoveryRoot(tmp_path),
        )
    )
    assert search.ok is True
    assert search.discovery is not None
    assert len(search.discovery.matches) > 0
    assert any(m.skill == "arxiv" for m in search.discovery.matches)
    assert search.discovery.warning
    assert search.discovery.warning_detail


def test_discover_fallback_on_empty_catalog(tmp_path):
    """E2E-DISCOVERY-004: empty catalog (skills not a list) -> tree scan fallback."""
    _seed_skills(tmp_path)
    catalog = SkillsCatalog()
    agent = SkillsDiscoveryAgent(
        catalog=catalog,
        discover=SkillsDiscover(catalog, SkillsBm25fRanker()),
        lister=SkillsLister(tmp_path),
        reader=SkillsPackReader(tmp_path),
    )

    # Write an empty (invalid) catalog payload so discover falls back.
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text('{"skills": "not-a-list"}', encoding="utf-8")

    search = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("arxiv papers"),
            root=DiscoveryRoot(tmp_path),
        )
    )
    assert search.ok is True
    assert search.discovery is not None
    assert len(search.discovery.matches) > 0
    assert any(m.skill == "arxiv" for m in search.discovery.matches)
    assert search.discovery.warning
    assert search.discovery.warning_detail


def test_discover_invalid_limit_e2e(tmp_path):
    """E2E-DISCOVERY-005: invalid limit flag through full agent returns exit_code 2."""
    _seed_skills(tmp_path)
    catalog = SkillsCatalog()
    agent = SkillsDiscoveryAgent(
        catalog=catalog,
        discover=SkillsDiscover(catalog, SkillsBm25fRanker()),
        lister=SkillsLister(tmp_path),
        reader=SkillsPackReader(tmp_path),
    )

    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("arxiv papers"),
            root=DiscoveryRoot(tmp_path),
            flags={"limit": "abc"},
        )
    )
    assert result.ok is False
    assert result.exit_code == 2
    assert "Invalid limit" in result.message


def test_discover_zero_match_returns_empty_list_exit_0(tmp_path):
    """E2E-DISCOVERY-006: valid query matching nothing -> empty matches + exit 0 (FR-discovery-004)."""
    _seed_skills(tmp_path)
    catalog = SkillsCatalog()
    agent = SkillsDiscoveryAgent(
        catalog=catalog,
        discover=SkillsDiscover(catalog, SkillsBm25fRanker()),
        lister=SkillsLister(tmp_path),
        reader=SkillsPackReader(tmp_path),
    )

    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.DISCOVER,
            query=DiscoveryQuery("zzznonexistentzzz"),
            root=DiscoveryRoot(tmp_path),
        )
    )
    assert result.ok is True
    assert result.exit_code == 0
    assert result.discovery is not None
    assert result.discovery.matches == ()
