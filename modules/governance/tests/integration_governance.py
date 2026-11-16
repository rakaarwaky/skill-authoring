"""Integration tests for modules/governance — agent + capability wiring."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from shared.src.governance.taxonomy_governance_request import (
    GovernanceRequest,
    GovernanceVerb,
    SkillQuery,
)


def _make_pack(tmp: Path, category: str, skill: str) -> Path:
    skill_dir = tmp / category / skill
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: skill\n---\n")
    return tmp


def test_agent_with_piner_capability_end_to_end():
    """IT-GOVERNANCE-001: agent + real piner toggles the pinned sidecar flag."""
    from governance.src.agent_governance_orchestrator import (
        SkillsGovernanceAgent,
    )
    from governance.src.capabilities_skills_piner import SkillsPiner

    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        _make_pack(pack, "cats", "my-skill")
        agent = SkillsGovernanceAgent(piner=SkillsPiner(), default_root=str(pack))
        agent.execute(
            GovernanceRequest(verb=GovernanceVerb.PIN, query=SkillQuery("my-skill"))
        )
        record = json.loads((pack / ".usage.json").read_text()).get("my-skill", {})
        assert record.get("pinned") is True, "piner must have set the pinned flag"


def test_mover_plan_move_is_pure_and_apply_move_writes():
    """IT-GOVERNANCE-002: mover.plan_move is pure, apply_move writes the move."""
    from governance.src.capabilities_skills_mover import SkillsMover

    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        _make_pack(pack, "cats", "my-skill")
        (pack / "dogs").mkdir()
        mover = SkillsMover()
        plan = mover.plan_move("my-skill", "dogs", pack)
        assert plan.kind == "move"
        assert plan.already_in_category is False
        outcome = mover.apply_move(plan)
        assert outcome.message
        assert (pack / "dogs" / "my-skill").is_dir()
        assert not (pack / "cats" / "my-skill").exists()


def test_mover_move_into_same_category_is_a_noop():
    """IT-GOVERNANCE-003: moving a skill into its own category is a no-op plan."""
    from governance.src.capabilities_skills_mover import SkillsMover

    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        _make_pack(pack, "cats", "my-skill")
        mover = SkillsMover()
        plan = mover.plan_move("my-skill", "cats", pack)
        assert plan.already_in_category is True
