"""Acceptance tests for modules/governance — map 1:1 to the FRD requirement ids.

Each test anchors one `FR-GOVERNANCE-NNN` requirement in `FRD.md`.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from shared.src.governance.taxonomy_governance_request import (
    GovernanceRequest,
    GovernanceVerb,
    SkillQuery,
)


def _make_agent(pack: Path):
    from governance.src.agent_governance_orchestrator import (
        SkillsGovernanceAgent,
    )
    from governance.src.capabilities_skills_mover import SkillsMover
    from governance.src.capabilities_skills_piner import SkillsPiner

    return SkillsGovernanceAgent(
        piner=SkillsPiner(),
        mover=SkillsMover(),
        default_root=str(pack),
    )


def test_fr_governance_001_pin_unpin_toggles_the_sidecar_flag():
    """AC-GOVERNANCE-001: FR-GOVERNANCE-001 — a pin/unpin pair
    returns the sidecar to its original state."""
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d) / "cats"
        skill_dir = pack / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")

        result = agent.execute(
            GovernanceRequest(verb=GovernanceVerb.PIN, query=SkillQuery("my-skill"))
        )
        assert result.ok, "pin should succeed"
        record = json.loads((pack / ".usage.json").read_text()).get("my-skill", {})
        assert record.get("pinned") is True

        result = agent.execute(
            GovernanceRequest(verb=GovernanceVerb.UNPIN, query=SkillQuery("my-skill"))
        )
        assert result.ok, "unpin should succeed"
        record = json.loads((pack / ".usage.json").read_text()).get("my-skill", {})
        assert record.get("pinned") is False


def test_fr_governance_002_move_rehomes_the_skill_inside_the_pack_root():
    """AC-GOVERNANCE-002: FR-GOVERNANCE-002 — a move into an existing
    target category re-homes the skill directory under the pack root."""
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        skill_dir = pack / "cats" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")
        (pack / "dogs").mkdir()

        agent = _make_agent(pack)
        result = agent.execute(
            GovernanceRequest(
                verb=GovernanceVerb.MOVE,
                query=SkillQuery("my-skill"),
                flags={"target": "dogs", "apply": "1"},
            )
        )
        assert result.ok is True
        assert (pack / "dogs" / "my-skill").is_dir()


def test_fr_governance_002_missing_target_flag_is_a_usage_error():
    """AC-GOVERNANCE-003: FR-GOVERNANCE-002 edge case — a MOVE request
    without a `--target` flag surfaces a usage error."""
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        skill_dir = pack / "cats" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")

        agent = _make_agent(pack)
        result = agent.execute(
            GovernanceRequest(verb=GovernanceVerb.MOVE, query=SkillQuery("my-skill"))
        )
        assert result.ok is False
        assert result.exit_code == 2
