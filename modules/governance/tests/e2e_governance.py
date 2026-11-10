"""E2E tests for modules/governance — full request lifecycle through the
agent with the real composition-root wiring and the real capabilities.

No mocks at the capability boundary: the agent is wired with the live
capability classes and drives requests end to end.
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
    from governance.src.agent_governance_orchestrator import SkillsGovernanceAgent
    from governance.src.capabilities_skills_locker import SkillsLocker
    from governance.src.capabilities_skills_mover import SkillsMover
    from governance.src.capabilities_skills_piner import SkillsPiner

    return SkillsGovernanceAgent(
        locker=SkillsLocker(),
        piner=SkillsPiner(),
        mover=SkillsMover(),
        default_root=str(pack),
    )


def test_e2e_lock_unlock_round_trip():
    """E2E-GOVERNANCE-001: lock + unlock returns the sidecar to its original state."""
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d) / "cats"
        skill_dir = pack / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")

        agent = _make_agent(pack)
        result = agent.execute(
            GovernanceRequest(verb=GovernanceVerb.LOCK, query=SkillQuery("my-skill"))
        )
        assert result.ok, "lock should succeed"
        record = json.loads((skill_dir / ".usage.json").read_text())
        assert record.get("locked") is True

        result = agent.execute(
            GovernanceRequest(verb=GovernanceVerb.UNLOCK, query=SkillQuery("my-skill"))
        )
        assert result.ok, "unlock should succeed"
        record = json.loads((skill_dir / ".usage.json").read_text())
        assert record.get("locked") is False


def test_e2e_move_to_existing_category():
    """E2E-GOVERNANCE-002: a move into an existing category re-homes the skill."""
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
        assert result.ok, "move should succeed"
        assert (pack / "dogs" / "my-skill").is_dir()
        assert not (pack / "cats" / "my-skill").exists()


def test_e2e_unknown_skill_returns_issues_found():
    """E2E-GOVERNANCE-003: locking a non-existent skill reports a failure result."""
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        agent = _make_agent(pack)
        result = agent.execute(
            GovernanceRequest(verb=GovernanceVerb.LOCK, query=SkillQuery("no-such-skill"))
        )
        assert result.ok is False
        assert result.exit_code == 1
