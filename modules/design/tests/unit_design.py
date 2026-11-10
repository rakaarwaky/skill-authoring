"""Design-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation.
"""

from __future__ import annotations

from design.src.agent_design_orchestrator import SkillsDesignAgent
from shared.src.design.taxonomy_design_request import SkillsOp, SkillsRequest
from shared.src.design.taxonomy_design_response import SkillsExitCode


def test_unknown_op_returns_usage_error() -> None:
    agent = SkillsDesignAgent()
    result = agent.execute(SkillsRequest(op=SkillsOp("bogus"), query=""))
    assert result.ok is False
    assert result.exit_code == SkillsExitCode.USAGE_ERROR


# ── Design capability unit tests ────────────────────────────────────────

def test_linter_category_filter_matches_only_in_scope() -> None:
    """UT-DESIGN-001: lint exit code reflects the filtered (in-scope) issue count."""
    from shared.src.design.taxonomy_design_vo import LintReport

    class FakeLinter:
        def lint(self, root, category=None):
            return LintReport(
                skills_root=root,
                issues=(),  # filtered: none in category X
                weed_lines=(),
                unfiltered_issues=("issue-a", "issue-b"),  # issues in other categories
                unfiltered_weed_lines=(),
            )

    agent = SkillsDesignAgent(linter=FakeLinter())
    result = agent.execute(
        SkillsRequest(op=SkillsOp.LINT, query="", flags={"category": "X"})
    )
    assert result.ok is True
    assert result.exit_code == SkillsExitCode.CLEAN


def test_mutate_skill_valueerror_becomes_usage_error() -> None:
    """UT-DESIGN-002: ValueError from adopter becomes a controlled SkillsResult exit 2."""

    class BadAdopter:
        def adopt(self, skill, root=None):
            raise ValueError("no skill directory found for: " + skill)

    agent = SkillsDesignAgent(adopter=BadAdopter())
    result = agent.execute(
        SkillsRequest(op=SkillsOp.ADOPT, query="missing-skill")
    )
    assert result.ok is False
    assert result.exit_code == SkillsExitCode.USAGE_ERROR
    assert "missing-skill" in result.message


def test_creator_path_traversal_rejected() -> None:
    """UT-DESIGN-003: create_skill refuses to write outside the skills root."""
    import tempfile
    from pathlib import Path

    from design.src.capabilities_skills_creator import SkillsCreator
    from shared.src.common.taxonomy_common_vo import SkillsRoot

    creator = SkillsCreator()
    with tempfile.TemporaryDirectory() as tmp:
        root = SkillsRoot(Path(tmp))
        try:
            creator.create_skill(
                skill="evil",
                category="../escape",
                description="d",
                when_to_use="",
                argument_hint="",
                body="",
                root=root,
                apply=True,
            )
        except Exception as exc:
            assert "outside the skills root" in str(exc)
            return
    raise AssertionError("expected SkillsUsageError for path traversal")


def test_creator_inside_root_writes_ok() -> None:
    """UT-DESIGN-004: create_skill writes inside the skills root when apply=True."""
    import tempfile
    from pathlib import Path

    from design.src.capabilities_skills_creator import SkillsCreator
    from shared.src.common.taxonomy_common_vo import SkillsRoot

    creator = SkillsCreator()
    with tempfile.TemporaryDirectory() as tmp:
        root = SkillsRoot(Path(tmp))
        (Path(tmp) / "cat").mkdir()
        plan = creator.create_skill(
            skill="my-skill",
            category="cat",
            description="d",
            when_to_use="",
            argument_hint="",
            body="body",
            root=root,
            apply=True,
        )
        assert plan.directory.exists()
        assert plan.skill_md.exists()
        text = plan.skill_md.read_text(encoding="utf-8")
        assert text.startswith("---\nname: my-skill\n")
        assert text.endswith("\n---\n\nbody")
