"""Design-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import cast

from design.src.agent_design_orchestrator import SkillsDesignAgent
from shared.src.design.taxonomy_design_request import SkillsOp, SkillsRequest
from shared.src.design.taxonomy_design_response import SkillsExitCode

# Canonical valid SKILL.md fixture — single source for the body-shape tests.
_VALID_SKILL_MD = (
    "---\nname: my-skill\n"
    'description: "a skill"\n'
    'when-to-use: "t"\n'
    'argument-hint: "h"\n'
    "---\n\n"
    "# My Skill\n\n"
    "You run this skill.\n\n"
    "## Rules\n\n"
    "| ID | Rule | Check |\n"
    "|----|------|-------|\n"
    "| R1 | x | y |\n\n"
    "## Routing\n\n"
    "| Scenario | File | Purpose |\n"
    "|------|------|---------|\n"
    "| 0 | ref.md | purpose |\n"
)


def _write_skill(root: Path, text: str) -> None:
    """Write *text* to <root>/cat/my-skill/SKILL.md, creating directories."""
    cat = root / "cat"
    cat.mkdir()
    skill_dir = cat / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")


def _lint_body(tmp: str, text: str):
    """Lint a SKILL.md written under *tmp*; return the LintReport."""
    from design.src.capabilities_skills_linter import SkillsLinter
    from shared.src.common.taxonomy_common_vo import SkillsRoot

    linter = SkillsLinter()
    _write_skill(Path(tmp), text)
    return linter.lint(SkillsRoot(Path(tmp)))


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
    from shared.src.design.taxonomy_design_vo import IssueType

    with tempfile.TemporaryDirectory() as tmp:
        text = (
            "---\nname: my-skill\n"
            'description: "a"\n'
            'when-to-use: "t"\n'
            'argument-hint: "h"\n'
            "---\n\n## Rules\n"
        )
        report = _lint_body(tmp, text)
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.MISSING_TITLE_HEADING.value in issue_types


def test_linter_flags_missing_frontmatter_keys() -> None:
    """UT-DESIGN-005: missing when-to-use or argument-hint flags issues."""
    from shared.src.design.taxonomy_design_vo import IssueType

    with tempfile.TemporaryDirectory() as tmp:
        # Valid shape minus when-to-use / argument-hint frontmatter keys.
        text = (
            "---\nname: my-skill\n"
            'description: "a skill"\n'
            "---\n\n" + _VALID_SKILL_MD.split("---\n\n", 1)[1]
        )
        report = _lint_body(tmp, text)
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.MISSING_WHEN_TO_USE.value in issue_types
        assert IssueType.MISSING_ARGUMENT_HINT.value in issue_types


def test_linter_passes_valid_shape() -> None:
    """UT-DESIGN-006: a valid SKILL.md raises no body-shape issues."""
    from shared.src.design.taxonomy_design_vo import IssueType

    with tempfile.TemporaryDirectory() as tmp:
        report = _lint_body(tmp, _VALID_SKILL_MD)
        # Body-shape IssueType members — derived from the enum, not a hand-maintained set.
        body_shape_types = {
            it.value
            for it in IssueType
            if it.name
            in (
                "MISSING_TITLE_HEADING",
                "MISSING_RULES_HEADING",
                "MISSING_ROUTING_HEADING",
                "DUPLICATE_TITLE_HEADING",
                "UNEXPECTED_HEADING",
                "RULES_TABLE_MISSING",
                "ROUTING_TABLE_MISSING",
                "MISSING_INTRO_PARAGRAPH",
                "MISSING_WHEN_TO_USE",
                "MISSING_ARGUMENT_HINT",
                "FORBIDDEN_DEEP_HEADING",
            )
        }
        body_shape_issues = {
            i.type for i in report.issues if i.type in body_shape_types
        }
        assert body_shape_issues == set()


def test_linter_flags_unexpected_heading() -> None:
    """UT-DESIGN-007: an extra H2 heading outside the template set flags unexpected-heading."""
    from shared.src.design.taxonomy_design_vo import IssueType

    with tempfile.TemporaryDirectory() as tmp:
        text = _VALID_SKILL_MD + "\n## Notes\n\nextra.\n"
        report = _lint_body(tmp, text)
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.UNEXPECTED_HEADING.value in issue_types
        unexpected_issues = [
            i for i in report.issues if i.type == IssueType.UNEXPECTED_HEADING.value
        ]
        assert len(unexpected_issues) == 1
        assert "## Notes" in unexpected_issues[0].message
        assert IssueType.MISSING_RULES_HEADING.value not in issue_types
        assert IssueType.MISSING_ROUTING_HEADING.value not in issue_types
        assert IssueType.DUPLICATE_TITLE_HEADING.value not in issue_types


def test_linter_flags_duplicate_h1() -> None:
    """UT-DESIGN-008: two H1 headings flag duplicate-title-heading."""
    from shared.src.design.taxonomy_design_vo import IssueType

    with tempfile.TemporaryDirectory() as tmp:
        text = _VALID_SKILL_MD.replace(
            "You run this skill.\n", "You run this skill.\n\n# My Skill\n"
        )
        report = _lint_body(tmp, text)
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.DUPLICATE_TITLE_HEADING.value in issue_types
        duplicate_issues = [
            i
            for i in report.issues
            if i.type == IssueType.DUPLICATE_TITLE_HEADING.value
        ]
        assert len(duplicate_issues) == 1
        assert "found 2 H1 heading(s)" in duplicate_issues[0].message
        assert IssueType.MISSING_TITLE_HEADING.value not in issue_types
        assert IssueType.UNEXPECTED_HEADING.value not in issue_types


def test_linter_lowercase_headings_pass() -> None:
    """UT-DESIGN-009: ## rules / ## routing lowercase match is accepted (case-insensitive)."""
    from shared.src.design.taxonomy_design_vo import IssueType

    with tempfile.TemporaryDirectory() as tmp:
        text = _VALID_SKILL_MD.replace("## Rules", "## rules").replace(
            "## Routing", "## routing"
        )
        report = _lint_body(tmp, text)
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.MISSING_RULES_HEADING.value not in issue_types
        assert IssueType.MISSING_ROUTING_HEADING.value not in issue_types
        assert IssueType.UNEXPECTED_HEADING.value not in issue_types


def test_linter_fuzzy_heading_rejected() -> None:
    """UT-DESIGN-010: ## Global Rules is not a fuzzy match — it flags both unexpected and missing."""
    from shared.src.design.taxonomy_design_vo import IssueType

    with tempfile.TemporaryDirectory() as tmp:
        text = _VALID_SKILL_MD.replace("## Rules", "## Global Rules")
        report = _lint_body(tmp, text)
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.UNEXPECTED_HEADING.value in issue_types
        assert IssueType.MISSING_RULES_HEADING.value in issue_types


def test_linter_flags_h3_heading() -> None:
    """UT-DESIGN-011: an H3 (###) heading flags forbidden-deep-heading."""
    from shared.src.design.taxonomy_design_vo import IssueType

    with tempfile.TemporaryDirectory() as tmp:
        text = _VALID_SKILL_MD + "\n### Sub\n\ncontent.\n"
        report = _lint_body(tmp, text)
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.FORBIDDEN_DEEP_HEADING.value in issue_types
        deep_issues = [
            i for i in report.issues if i.type == IssueType.FORBIDDEN_DEEP_HEADING.value
        ]
        assert len(deep_issues) == 1
        assert "### Sub" in deep_issues[0].message
        assert IssueType.UNEXPECTED_HEADING.value not in issue_types


def test_linter_flags_h4_heading() -> None:
    """UT-DESIGN-012: an H4 (####) heading flags forbidden-deep-heading."""
    from shared.src.design.taxonomy_design_vo import IssueType

    with tempfile.TemporaryDirectory() as tmp:
        text = _VALID_SKILL_MD + "\n#### Deep\n\ncontent.\n"
        report = _lint_body(tmp, text)
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.FORBIDDEN_DEEP_HEADING.value in issue_types
        deep_issues = [
            i for i in report.issues if i.type == IssueType.FORBIDDEN_DEEP_HEADING.value
        ]
        assert len(deep_issues) == 1
        assert "#### Deep" in deep_issues[0].message
        assert IssueType.UNEXPECTED_HEADING.value not in issue_types


def test_linter_flags_h5_and_h6_headings() -> None:
    """UT-DESIGN-013: H5 (#####) and H6 (######) headings flag forbidden-deep-heading."""
    from shared.src.design.taxonomy_design_vo import IssueType

    with tempfile.TemporaryDirectory() as tmp:
        text = _VALID_SKILL_MD + "\n##### H5\n\ncontent.\n\n###### H6\n\nmore.\n"
        report = _lint_body(tmp, text)
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.FORBIDDEN_DEEP_HEADING.value in issue_types
        deep_issues = [
            i for i in report.issues if i.type == IssueType.FORBIDDEN_DEEP_HEADING.value
        ]
        assert len(deep_issues) == 1
        assert "##### H5" in deep_issues[0].message
        assert "###### H6" in deep_issues[0].message
        assert IssueType.UNEXPECTED_HEADING.value not in issue_types


def test_linter_flags_multiple_deep_headings() -> None:
    """UT-DESIGN-014: multiple deep headings in one file are all reported together."""
    from shared.src.design.taxonomy_design_vo import IssueType

    with tempfile.TemporaryDirectory() as tmp:
        text = _VALID_SKILL_MD + "\n### A\n\ntext.\n\n### B\n\nmore.\n"
        report = _lint_body(tmp, text)
        issue_types = {issue.type for issue in report.issues}
        assert IssueType.FORBIDDEN_DEEP_HEADING.value in issue_types
        deep_issues = [
            i for i in report.issues if i.type == IssueType.FORBIDDEN_DEEP_HEADING.value
        ]
        assert len(deep_issues) == 1
        assert "### A" in deep_issues[0].message
        assert "### B" in deep_issues[0].message
        assert IssueType.UNEXPECTED_HEADING.value not in issue_types
