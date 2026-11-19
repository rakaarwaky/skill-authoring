"""Skills linter capability (AES capabilities layer).

Implements ``ISkillsLinterProtocol``: a combined scan that runs the
13-rule validator plus the weed report in one pass, returning a single
``LintReport``. The lint is read-only — it reports, it never writes.

The lint supports an optional *category* filter: when provided, only
issues whose ``category`` or ``path`` belongs to that category are
included in the report. The weed lines are not filtered (they are
library-wide duplicate/empty-category signals).

The 13-rule checks run inline here, ported from the retired
``capabilities_skills_validator.py`` which was folded into this
capability during the deep-clean. Rule IDs and message templates come
from the shared rule SSOT, so the checker and the generated rules doc
cannot drift apart. The weed-plan is consumed through the shared
``utility_skills_mutation.plan_weed`` helper, never through a sibling
capability import.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from shared.src.common.taxonomy_common_constant import (
    ASSETS_MARKER_FILENAME,
    CATALOG_FILENAME,
    IGNORED_CATEGORY_DIRS,
    PACK_MARKER_FILENAME,
)
from shared.src.common.taxonomy_common_entity import (
    CategorySummary,
    SkillEntry,
)
from shared.src.common.taxonomy_common_vo import SkillsRoot
from shared.src.design.contract_design_protocol import ISkillsLinterProtocol
from shared.src.design.taxonomy_design_constant import (
    MAX_DESCRIPTION_LEN,
    MAX_WHEN_TO_USE_LEN,
)
from shared.src.design.taxonomy_design_entity import (
    Issue,
)
from shared.src.design.taxonomy_design_vo import (
    IssueType,
    LintReport,
    ValidationReport,
    is_valid_skill_name,
    issue_message,
)
from shared.src.discovery.utility_discovery_core import (
    category_dirs,
    category_summaries,
    parse_frontmatter,
    relpath,
    skill_entries,
)
from shared.src.maintenance.utility_skills_mutation import plan_weed

__all__ = ["SkillsLinter"]


# ─── Block 1: Module Declaration ───
class SkillsLinter(ISkillsLinterProtocol):
    """Combined lint: 13-rule checks + weed report, optionally category-filtered."""

    # ─── Block 2: Module Contract ───
    def lint(
        self, root: SkillsRoot, category: str | None = None
    ) -> LintReport:
        """Run the full lint over *root*; optionally filter by *category*.

        Runs the 13-rule validator (per-skill, category, placement, and
        duplicate checks) inline plus the shared ``plan_weed`` helper for
        the weed lines. When *category* is set, issues are narrowed to
        that category; weed lines are kept as-is (library-wide signals).
        """
        skills_root = Path(root)

        # 13-rule validator checks
        entries = skill_entries(skills_root)
        categories = category_summaries(entries, skills_root)
        assets = assets_container(skills_root)

        issues: list[Issue] = []

        self._check_categories(categories, assets, issues)
        self._check_entries(skills_root, entries, issues)
        self._check_placement(skills_root, issues)
        self._check_duplicates(entries, issues)
        self._check_references(skills_root, entries, issues)
        self._check_body_shape(skills_root, entries, issues)

        report = ValidationReport(
            skills_root=skills_root,
            catalog=skills_root / CATALOG_FILENAME,
            issues=tuple(issues),
            skills=len(entries),
            categories=len(list(category_dirs(skills_root))),
        )

        # Weed report
        weed_plan = plan_weed(skills_root)
        weed_lines = weed_plan.lines

        # Category filter
        unfiltered_issues = report.issues
        unfiltered_weed_lines = weed_lines
        if category is not None:
            issues = tuple(
                issue
                for issue in report.issues
                if issue.category == category
                or (issue.path or "").startswith(f"{category}/")
                # Library-wide issues carry neither a category nor a path
                # (duplicate-name / duplicate-description). They are kept
                # in every category-filtered report so cross-category
                # duplicate collisions remain visible.
                or (issue.category is None and (issue.path or "") == "")
            )
        else:
            issues = report.issues

        return LintReport(
            skills_root=skills_root,
            issues=issues,
            weed_lines=weed_lines,
            skills=report.skills,
            categories=report.categories,
            unfiltered_issues=unfiltered_issues,
            unfiltered_weed_lines=unfiltered_weed_lines,
        )

    # ─── Block 3: Module Helpers ───

    @staticmethod
    def _check_categories(
        categories: list[CategorySummary],
        assets: set[str],
        issues: list[Issue],
    ) -> None:
        """Category-shape checks, skipping declared DM2 asset containers."""
        for cat in categories:
            if cat.category in assets:
                continue

            if not cat.description_file_exists:
                issues.append(
                    Issue(
                        type=IssueType.MISSING_CATEGORY_DESCRIPTION.value,
                        message=issue_message(IssueType.MISSING_CATEGORY_DESCRIPTION),
                        category=cat.category,
                    )
                )
            elif not cat.description:
                issues.append(
                    Issue(
                        type=IssueType.EMPTY_CATEGORY_DESCRIPTION.value,
                        message=issue_message(IssueType.EMPTY_CATEGORY_DESCRIPTION),
                        category=cat.category,
                    )
                )

            if cat.skill_count == 0:
                issues.append(
                    Issue(
                        type=IssueType.EMPTY_CATEGORY.value,
                        message=issue_message(IssueType.EMPTY_CATEGORY),
                        category=cat.category,
                    )
                )

    @staticmethod
    def _check_entries(
        skills_root: Path,
        entries: list[SkillEntry],
        issues: list[Issue],
    ) -> None:
        """Per-skill checks: name, description, budget, and nesting."""
        for entry in entries:
            if entry.frontmatter_name != entry.skill:
                issues.append(
                    Issue(
                        type=IssueType.NAME_MISMATCH.value,
                        message=issue_message(
                            IssueType.NAME_MISMATCH,
                            name=entry.frontmatter_name,
                            dir=entry.skill,
                        ),
                        path=entry.path,
                    )
                )

            if not is_valid_skill_name(entry.skill):
                issues.append(
                    Issue(
                        type=IssueType.INVALID_SKILL_NAME.value,
                        message=issue_message(IssueType.INVALID_SKILL_NAME),
                        path=entry.path,
                    )
                )

            if not entry.description:
                issues.append(
                    Issue(
                        type=IssueType.MISSING_DESCRIPTION.value,
                        message=issue_message(IssueType.MISSING_DESCRIPTION),
                        path=entry.path,
                    )
                )
            else:
                if any(ch in entry.description for ch in ('<', '>', '"')):
                    issues.append(
                        Issue(
                            type=IssueType.INVALID_DESCRIPTION_CHARACTERS.value,
                            message=issue_message(
                                IssueType.INVALID_DESCRIPTION_CHARACTERS
                            ),
                            path=entry.path,
                        )
                    )

                if len(entry.description) > MAX_DESCRIPTION_LEN:
                    issues.append(
                        Issue(
                            type=IssueType.DESCRIPTION_TOO_LONG.value,
                            message=issue_message(
                                IssueType.DESCRIPTION_TOO_LONG,
                                length=len(entry.description),
                                max_len=MAX_DESCRIPTION_LEN,
                            ),
                            path=entry.path,
                        )
                    )

            if not entry.when_to_use:
                issues.append(
                    Issue(
                        type=IssueType.MISSING_WHEN_TO_USE.value,
                        message=issue_message(IssueType.MISSING_WHEN_TO_USE),
                        path=entry.path,
                    )
                )
            elif len(entry.when_to_use) > MAX_WHEN_TO_USE_LEN:
                issues.append(
                    Issue(
                        type=IssueType.WHEN_TO_USE_TOO_LONG.value,
                        message=issue_message(
                            IssueType.WHEN_TO_USE_TOO_LONG,
                            length=len(entry.when_to_use),
                            max_len=MAX_WHEN_TO_USE_LEN,
                        ),
                        path=entry.path,
                    )
                )

    @staticmethod
    def _check_placement(skills_root: Path, issues: list[Issue]) -> None:
        """``SKILL.md`` directly under a category, and too-deep files."""
        for path in iter_relative_skill_mds(skills_root, depth=1):
            issues.append(
                Issue(
                    type=IssueType.INVALID_PLACEMENT.value,
                    message=issue_message(IssueType.INVALID_PLACEMENT),
                    path=relpath(path, skills_root),
                )
            )

        exempt = too_deep_exempt_paths(skills_root)
        # Walk the full subtree at min-depth 3 so any SKILL.md deeper than
        # category/skill/SKILL.md (depth >= 3, including depth 4+) is
        # flagged TOO_DEEP per the rule SSOT (no nesting deeper than
        # category/skill/SKILL.md). Without this a SKILL.md at depth 4+
        # would silently escape the rule.
        for path in iter_relative_skill_mds(skills_root, min_depth=3):
            # DM1 nested-pack marker: the intermediate directory carrying
            # ``pack.toml`` opts the pack in — its too-deep files are
            # skipped. Without the marker the violation stands unchanged.
            if relpath(path, skills_root) in exempt:
                continue
            issues.append(
                Issue(
                    type=IssueType.TOO_DEEP.value,
                    message=issue_message(IssueType.TOO_DEEP),
                    path=relpath(path, skills_root),
                )
            )

    @staticmethod
    def _check_duplicates(entries: list[SkillEntry], issues: list[Issue]) -> None:
        """Library-wide duplicate names and descriptions."""
        name_map: dict[str, list[str]] = {}
        desc_map: dict[str, list[str]] = {}

        for entry in entries:
            name_map.setdefault(entry.skill, []).append(entry.path)
            if entry.description:
                desc_map.setdefault(entry.description, []).append(entry.path)

        for name, paths in sorted(name_map.items()):
            if len(paths) > 1:
                issues.append(
                    Issue(
                        type=IssueType.DUPLICATE_SKILL_NAME.value,
                        message=issue_message(
                            IssueType.DUPLICATE_SKILL_NAME,
                            name=name,
                            paths=", ".join(sorted(paths)),
                        ),
                    )
                )

        for description, paths in sorted(desc_map.items()):
            if len(paths) > 1:
                issues.append(
                    Issue(
                        type=IssueType.DUPLICATE_DESCRIPTION.value,
                        message=issue_message(
                            IssueType.DUPLICATE_DESCRIPTION,
                            paths=", ".join(sorted(paths)),
                        ),
                    )
                )

    @staticmethod
    def _check_references(
        skills_root: Path,
        entries: list[SkillEntry],
        issues: list[Issue],
    ) -> None:
        """Every file in a skill's ``references/`` must be linked from SKILL.md."""
        for entry in entries:
            skill_dir = skills_root / entry.path
            references_dir = skill_dir / "references"
            if not references_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue
            # Tolerate a corrupt or unreadable SKILL.md: decode with
            # errors="replace" (consistent with parse_frontmatter) and skip
            # the reference check for this entry on OSError so one bad file
            # cannot abort the whole lint scan.
            try:
                body = skill_md.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue

            unlinked: list[str] = []
            for ref_path in iter_files(references_dir):
                ref_name = ref_path.name
                # A reference is "linked" if its filename appears anywhere in SKILL.md.
                if ref_name not in body:
                    unlinked.append(
                        relpath(ref_path, skills_root)
                    )

            if unlinked:
                issues.append(
                    Issue(
                        type=IssueType.REFERENCE_NOT_LINKED.value,
                        message=issue_message(
                            IssueType.REFERENCE_NOT_LINKED,
                            paths=", ".join(sorted(unlinked)),
                        ),
                        path=entry.path,
                    )
                )

    @staticmethod
    def _check_body_shape(
        skills_root: Path,
        entries: list[SkillEntry],
        issues: list[Issue],
    ) -> None:
        """Check body shape: frontmatter keys, headings, tables, intro paragraph."""
        for entry in entries:
            skill_dir = skills_root / entry.path
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue

            try:
                text = skill_md.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue

            # Check argument-hint in frontmatter
            frontmatter = parse_frontmatter(skill_md)
            if not frontmatter.get("argument-hint"):
                issues.append(
                    Issue(
                        type=IssueType.MISSING_ARGUMENT_HINT.value,
                        message=issue_message(IssueType.MISSING_ARGUMENT_HINT),
                        path=entry.path,
                    )
                )

            # Split frontmatter and body
            stripped = text.lstrip()
            if not stripped.startswith("---"):
                continue
            parts = stripped.split("---", 2)
            if len(parts) < 3:
                continue
            body = parts[2]

            body_lines = [line.strip() for line in body.splitlines()]

            # 1. Heading check:
            # First heading must be `# <Skill Name>`
            # Then `## Rules` and `## Routing`
            h1_lines = [l for l in body_lines if l.startswith("# ")]
            h2_lines = [l for l in body_lines if l.startswith("## ")]

            if not h1_lines:
                issues.append(
                    Issue(
                        type=IssueType.MISSING_TITLE_HEADING.value,
                        message=issue_message(IssueType.MISSING_TITLE_HEADING),
                        path=entry.path,
                    )
                )

            # Check ## Rules heading
            has_rules_h2 = any(l.lower().startswith("## rules") or l.lower().startswith("## global rules") for l in h2_lines)
            if not has_rules_h2:
                issues.append(
                    Issue(
                        type=IssueType.MISSING_RULES_HEADING.value,
                        message=issue_message(IssueType.MISSING_RULES_HEADING),
                        path=entry.path,
                    )
                )

            # Check ## Routing heading
            has_routing_h2 = any(
                l.lower().startswith("## routing")
                or l.lower().startswith("## steps")
                or "routing" in l.lower()
                for l in h2_lines
            )
            if not has_routing_h2:
                issues.append(
                    Issue(
                        type=IssueType.MISSING_ROUTING_HEADING.value,
                        message=issue_message(IssueType.MISSING_ROUTING_HEADING),
                        path=entry.path,
                    )
                )

            # 2. Table checks:
            # Rules table: | ID | Rule | Check |
            has_rules_table = False
            has_routing_table = False
            for l in body_lines:
                if l.startswith("|") and l.endswith("|"):
                    cells = [c.strip().lower() for c in l.split("|")[1:-1]]
                    if "id" in cells and "rule" in cells and ("check" in cells or "why" in cells):
                        has_rules_table = True
                    routing_col1 = any(any(k in c for k in ["step", "file", "files", "reference", "scenario", "document", "subcommand", "workflow", "use case", "task", "rule code", "user wants"]) for c in cells)
                    routing_col2 = any(any(k in c for k in ["purpose", "description", "action", "files", "load", "focus", "what it checks", "reference"]) for c in cells)
                    if len(cells) >= 2 and (routing_col1 or routing_col2):
                        has_routing_table = True

            if not has_rules_table:
                issues.append(
                    Issue(
                        type=IssueType.RULES_TABLE_MISSING.value,
                        message=issue_message(IssueType.RULES_TABLE_MISSING),
                        path=entry.path,
                    )
                )

            if not has_routing_table:
                issues.append(
                    Issue(
                        type=IssueType.ROUTING_TABLE_MISSING.value,
                        message=issue_message(IssueType.ROUTING_TABLE_MISSING),
                        path=entry.path,
                    )
                )

            # 3. Paragraph explanation below # <Skill Name>
            # There should be non-empty paragraph text before the first ## heading
            found_h1 = False
            intro_lines: list[str] = []
            for line in body_lines:
                if line.startswith("# "):
                    found_h1 = True
                    continue
                if found_h1:
                    if line.startswith("## "):
                        break
                    if line and not line.startswith("#"):
                        intro_lines.append(line)

            if not intro_lines:
                issues.append(
                    Issue(
                        type=IssueType.MISSING_INTRO_PARAGRAPH.value,
                        message=issue_message(IssueType.MISSING_INTRO_PARAGRAPH),
                        path=entry.path,
                    )
                )


# Linter-local tree walkers (single-consumer, moved out of utility)

def assets_container(skills_root: Path) -> set[str]:
    """Category names that carry a declared DM2 asset-container marker.

    Linter-only: checks each non-ignored category directory for an
    ``ASSETS_MARKER_FILENAME`` whose frontmatter ``kind`` is ``assets``.
    """
    declared: set[str] = set()
    for category in category_dirs(skills_root):
        marker = category / ASSETS_MARKER_FILENAME
        if not marker.is_file():
            continue
        frontmatter = parse_frontmatter(marker)
        if frontmatter.get("kind") == "assets":
            declared.add(category.name)
    return declared


def iter_files(folder: Path) -> Iterator[Path]:
    """Yield every regular file under ``folder`` without following symlinks.

    Linter-only: deterministic (sorted names per directory); symlinked
    directories are listed but never descended, so a loop cannot hang
    the scan.
    """
    if not folder.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(folder, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            yield Path(dirpath) / name


def iter_relative_skill_mds(
    skills_root: Path,
    *,
    depth: int | None = None,
    min_depth: int | None = None,
) -> Iterator[Path]:
    """Yield ``SKILL.md`` files below the root, filtered by depth.

    Linter-only. Exactly one of *depth* / *min_depth* must be given:

    * *depth* (exact) yields files exactly ``depth`` directories below the
      root. ``depth=1`` is ``category/SKILL.md`` (invalid placement);
      ``depth=3`` is ``category/pack/nested/SKILL.md`` (too deep).
    * *min_depth* (floor) walks the full subtree and yields every
      ``SKILL.md`` whose path is at least ``min_depth`` directories below
      the root (e.g. ``min_depth=3`` catches too-deep files at depth 4+,
      not just depth 3).

    Hidden and ignored category directories are skipped. Symlinked
    files are not descended into (a ``SKILL.md`` reachable only via a
    symlink is not yielded), so a symlink loop cannot hang the scan.
    """
    if (depth is None) == (min_depth is None):
        raise ValueError("Provide exactly one of depth= or min_depth=")

    if min_depth is not None:
        for category in category_dirs(skills_root):
            for path in category.rglob("SKILL.md"):
                try:
                    rel = path.relative_to(skills_root)
                except ValueError:
                    continue
                parts = rel.parts
                if len(parts) - 1 < min_depth:
                    continue
                if any(p.startswith(".") for p in parts):
                    continue
                if any(p == "tools" or p in IGNORED_CATEGORY_DIRS for p in parts):
                    continue
                yield path
        return

    # Exact-depth path (depth=1 for invalid placement, depth=3 for too-deep).
    pattern = "/".join(["*"] * depth + ["SKILL.md"])
    for path in skills_root.glob(pattern):
        try:
            rel = path.relative_to(skills_root)
        except ValueError:
            continue
        parts = rel.parts
        if not parts:
            continue
        if parts[0].startswith("."):
            continue
        if parts[0] in IGNORED_CATEGORY_DIRS:
            continue
        yield path


def too_deep_exempt_paths(skills_root: Path) -> set[str]:
    """DM1 nested-pack exemption: ``category/pack/SKILL.md`` paths whose
    intermediate directory carries the ``pack.toml`` marker."""
    exempt: set[str] = set()
    for category in category_dirs(skills_root):
        for skill_md in category.glob("*/*/SKILL.md"):
            marker = skill_md.parent.parent / PACK_MARKER_FILENAME
            if marker.is_file():
                try:
                    exempt.add(str(skill_md.relative_to(skills_root)))
                except ValueError:
                    continue
    return exempt
