"""Design-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation.
"""

from __future__ import annotations

from typing import cast

from design.src.agent_design_orchestrator import SkillsDesignAgent
from shared.src.design.taxonomy_design_request import SkillsOp, SkillsRequest
from shared.src.design.taxonomy_design_response import SkillsExitCode


def test_unknown_op_returns_usage_error() -> None:
    agent = SkillsDesignAgent()
    result = agent.execute(SkillsRequest(op=cast(SkillsOp, "bogus"), query=""))
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


def test_creator_path_traversal_rejected() -> None:
    """UT-DESIGN-002: create_skill refuses to write outside the skills root."""
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


def test_iter_relative_skill_mds_min_depth() -> None:
    """UT-DESIGN-003: min_depth=3 yields depth >= 3 and skips standard category/skill/SKILL.md."""
    import tempfile
    from pathlib import Path
    from design.src.capabilities_skills_linter import iter_relative_skill_mds

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # standard skill (depth 2): category/skill/SKILL.md
        std = root / "cat" / "skill" / "SKILL.md"
        std.parent.mkdir(parents=True)
        std.write_text("# std")

        # too-deep skill (depth 3): category/pack/nested/SKILL.md
        too_deep = root / "cat" / "pack" / "nested" / "SKILL.md"
        too_deep.parent.mkdir(parents=True)
        too_deep.write_text("# deep")

        # invalid placement (depth 1): category/SKILL.md
        invalid = root / "cat" / "SKILL.md"
        invalid.write_text("# invalid")

        results = list(iter_relative_skill_mds(root, min_depth=3))
        assert too_deep in results
        assert std not in results
        assert invalid not in results


def test_creator_inside_root_writes_ok() -> None:
    """UT-DESIGN-003: create_skill writes inside the skills root when apply=True."""
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


# ── Body-shape linter unit tests ───────────────────────────────────

def test_linter_flags_missing_title_heading() -> None:
    """UT-DESIGN-004: missing '# <Skill Name>' heading raises missing-title-heading."""
    import tempfile
    from pathlib import Path

    from design.src.capabilities_skills_linter import SkillsLinter
    from shared.src.common.taxonomy_common_vo import SkillsRoot
    from shared.src.design.taxonomy_design_vo import IssueType

    linter = SkillsLinter()
    with tempfile.TemporaryDirectory() as tmp:
        cat = Path(tmp) / "cat"
        cat.mkdir()
        skill_dir = cat / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\n"
            'description: "a"\n'
            "when-to-use: \"t\"\n"
            "argument-hint: \"h\"\n"
            "---\n\n## Rules\n",
            encoding="utf-8",
        )
        report = linter.lint(SkillsRoot(Path(tmp)))
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.MISSING_TITLE_HEADING in issue_types or IssueType.MISSING_TITLE_HEADING.value in issue_types


def test_linter_flags_missing_frontmatter_keys() -> None:
    """UT-DESIGN-005: missing when-to-use or argument-hint flags issues."""
    import tempfile
    from pathlib import Path

    from design.src.capabilities_skills_linter import SkillsLinter
    from shared.src.common.taxonomy_common_vo import SkillsRoot
    from shared.src.design.taxonomy_design_vo import IssueType

    linter = SkillsLinter()
    with tempfile.TemporaryDirectory() as tmp:
        cat = Path(tmp) / "cat"
        cat.mkdir()
        skill_dir = cat / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\n"
            'description: "a"\n'
            "---\n\n# My Skill\n\nIntro.\n\n## Rules\n\n| ID | Rule | Check |\n|---|---|---|\n\n## Routing\n\n| Step | File | Purpose |\n|---|---|---|\n",
            encoding="utf-8",
        )
        report = linter.lint(SkillsRoot(Path(tmp)))
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.MISSING_WHEN_TO_USE.value in issue_types
        assert IssueType.MISSING_ARGUMENT_HINT.value in issue_types


def test_linter_passes_valid_shape() -> None:
    """UT-DESIGN-006: a valid SKILL.md raises no body-shape issues."""
    import tempfile
    from pathlib import Path

    from design.src.capabilities_skills_linter import SkillsLinter
    from shared.src.common.taxonomy_common_vo import SkillsRoot

    linter = SkillsLinter()
    with tempfile.TemporaryDirectory() as tmp:
        cat = Path(tmp) / "cat"
        cat.mkdir()
        skill_dir = cat / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\n"
            'description: "a skill"\n'
            "when-to-use: \"t\"\n"
            "argument-hint: \"h\"\n"
            "---\n\n# My Skill\n\nYou run this skill.\n\n## Rules\n\n| ID | Rule | Check |\n|----|------|-------|\n| R1 | x | y |\n\n## Routing\n\n| Step | File | Purpose |\n|------|------|---------|\n| 0 | ref.md | purpose |\n",
            encoding="utf-8",
        )
        report = linter.lint(SkillsRoot(Path(tmp)))
        body_shape_issues = {
            issue.type for issue in report.issues
            if getattr(issue.type, "value", issue.type) in {
                "missing-title-heading", "missing-rules-heading",
                "missing-routing-heading", "rules-table-missing",
                "routing-table-missing", "missing-intro-paragraph",
                "missing-when-to-use", "missing-argument-hint",
            }
        }
        assert body_shape_issues == set()
