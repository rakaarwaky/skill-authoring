"""SSOT for skill-library validation rules (AES taxonomy layer).

The single executable source of truth for what a valid skill is: the
budget / layout constants, the escape helpers' rule text, the layout
invariants, and the issue taxonomy — the 13 issue-type strings plus the
exact message strings ``validate`` emits. It also carries the rule-doc
summaries/citations, and the lifecycle state constants.

Cross-domain shared constants (naming budget, category dirs, catalog
file, drift warning, BM25F scale) live in
``shared.src.common.taxonomy_common_constant``.

Provenance: these values originated in the retired ``librarian.py``
(which no longer exists); this module is now the single executable
source of truth. Nothing in it is re-derivable from elsewhere: every
consumer (the validator capability and the skill-rules reference doc)
must read these constants rather than restate them.
"""

from __future__ import annotations

from typing import Final

# Originally ``librarian.py`` (retired); now this module is the SSOT.
MAX_DESCRIPTION_LEN: Final = 1024
MAX_WHEN_TO_USE_LEN: Final = 1024

# ── Rule documentation ───────────────────────────────────────────────

#: One-line summaries for the skill-rules reference doc headings.
#: Short imperatives; the full constraint text is the verbatim
#: ``ISSUE_MESSAGES`` template in ``taxonomy_design_vo.py``.
SUMMARIES: Final = {
    "name-mismatch": "Frontmatter `name:` equals the skill directory name",
    "name-format": "Skill names are lowercase letters, digits, and hyphens",
    "description-present": "Every skill carries a `description:`",
    "description-characters": "Descriptions contain no `<`, `>`, or `\"`",
    "description-length": "Descriptions are at most 1024 characters",
    "skill-placement": "`SKILL.md` lives at `<category>/<skill>/SKILL.md`",
    "category-depth": "No nesting deeper than `<category>/<skill>/`",
    "unique-skill-name": "Each skill name is used by one folder only",
    "unique-description": "No two skills share one description",
    "category-description-present": "Every category has a `DESCRIPTION.md`",
    "category-description-nonempty": "Category `DESCRIPTION.md` describes the category",
    "category-nonempty": "Every category holds at least one skill",
    "references-linked": "Every file in `references/` is linked from `SKILL.md`",
    "when-to-use-length": "When-to-use strings are at most 1024 characters",
    "when-to-use-present": "Every skill carries a `when-to-use:` frontmatter key",
    "argument-hint-present": "Every skill carries an `argument-hint:` frontmatter key",
    "title-heading": "SKILL.md starts with a `# <Skill Name>` heading",
    "rules-heading": "SKILL.md carries a `## Rules` heading",
    "routing-heading": "SKILL.md carries a `## Routing` heading",
    "duplicate-title-heading": "SKILL.md has exactly one `# <Skill Name>` H1 heading",
    "unexpected-heading": "SKILL.md carries only `## Rules` and `## Routing` as H2 headings",
    "rules-table": "## Rules carries a table with `| ID | Rule | Check |` header",
    "routing-table": "## Routing carries a table with `| Scenario | File | Purpose |` header",
    "intro-paragraph": "SKILL.md contains an explanation paragraph under `# <Skill Name>`",
}

#: Loader citations: the file each constraint was first read from. Empty
#: where no real citation exists — provenance that cannot be traced to a
#: source is left to the skill-rules reference doc to discuss, never invented here.
CITATIONS: Final = {
    "name-mismatch": "`create-skills/SKILL.md` (name must equal the directory)",
    "name-format": (
        "`create-skills/SKILL.md` and `create-skills/references/"
        "validation-criteria.md` (both stated the name alphabet)"
    ),
    "description-present": "`create-skills/SKILL.md` (required frontmatter shape)",
    "description-characters": (
        "`create-skills/SKILL.md` (Grok Build embeds the value in "
        "`<skill description=\"...\">`)"
    ),
    "description-length": (
        "`create-skills/SKILL.md` and `validation-criteria.md` "
        "(both stated the 1,024-char ceiling)"
    ),
    "skill-placement": (
        "`create-skills/SKILL.md` (placement rule) and "
        "`skill-librarian/references/category-rules.md` (folder shape)"
    ),
    "category-depth": (
        "`create-skills/SKILL.md` (loaders walk one level) and "
        "`category-rules.md` (no nested subcategories)"
    ),
    "unique-skill-name": "",
    "unique-description": "",
    "category-description-present": (
        "`skill-librarian/references/category-rules.md` (DESCRIPTION.md section)"
    ),
    "category-description-nonempty": (
        "`skill-librarian/references/category-rules.md` "
        "(the description decides where skills belong)"
    ),
    "category-nonempty": "",
    "references-linked": (
        "`SKILL.md` body or Routing table must name every `references/` file"
    ),
    "when-to-use-length": "`skill-improve/references/step-1-format.md` (1024-char limit)",
    "when-to-use-present": "`template/skill.md` (mandatory frontmatter key)",
    "argument-hint-present": "`template/skill.md` (mandatory frontmatter key)",
    "title-heading": "`template/skill.md` (exact body heading shape)",
    "rules-heading": "`template/skill.md` (exact body heading shape)",
    "routing-heading": "`template/skill.md` (exact body heading shape)",
    "duplicate-title-heading": "`template/skill.md` (exactly one H1 heading)",
    "unexpected-heading": "`template/skill.md` (only `## Rules` and `## Routing` allowed)",
    "rules-table": "`template/skill.md` (Rules table columns)",
    "routing-table": "`template/skill.md` (Routing table columns)",
    "intro-paragraph": "`template/skill.md` (one paragraph explanation under title)",
}

# ── Lifecycle ────────────────────────────────────────────────────────

#: Lifecycle states a skill can hold.
LIFECYCLE_STATES: Final = ("active", "stale", "archived")

__all__ = [
    "CITATIONS",
    "LIFECYCLE_STATES",
    "MAX_DESCRIPTION_LEN",
    "MAX_WHEN_TO_USE_LEN",
    "SUMMARIES",
]
