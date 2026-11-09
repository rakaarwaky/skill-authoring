"""Skills design-domain capability contracts (AES contract layer, ABC traits).

One seam per design-side capability: adopter, creator, linter, runner.
Capabilities in ``modules/design/src`` implement these; the composition
root injects them into the agent. No import of sibling domain contracts —
design keeps its own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.common.taxonomy_common_vo import CategoryName, SkillName
from shared.src.common.taxonomy_common_vo import SkillsRoot
from shared.src.design.taxonomy_design_vo import (
    LintReport,
    MutationOutcome,
    NewCategoryPlan,
    SkillCreatePlan,
)


class ISkillsAdopterProtocol(ABC):
    """Adopter capability: adopt verb."""

    @abstractmethod
    def adopt(
        self, skill: SkillName, root: SkillsRoot | None = None
    ) -> MutationOutcome:
        """Mark *skill* as agent-managed (``created_by="agent"``)."""
        ...


class ISkillsCreatorProtocol(ABC):
    """Create skills and categories in the pack (dry-run by default)."""

    @abstractmethod
    def create_skill(
        self,
        skill: SkillName,
        category: str,
        description: str,
        when_to_use: str,
        argument_hint: str,
        body: str,
        root: SkillsRoot,
        apply: bool,
    ) -> SkillCreatePlan:
        """Plan (or apply) creating a new skill SKILL.md.

        When ``apply`` is False the returned plan is a preview.
        When True, the file is written.
        """
        ...

    @abstractmethod
    def create_category(
        self,
        name: CategoryName,
        description: str,
        root: SkillsRoot,
        force: bool,
        apply: bool,
    ) -> NewCategoryPlan:
        """Plan (or apply) creating a category folder + DESCRIPTION.md.

        When ``apply`` is False the returned plan is a preview.
        When True, the directory and description file are written.
        """
        ...


class ISkillsLinterProtocol(ABC):
    """Combined lint scan: 13-rule checks + weed report in one pass."""

    @abstractmethod
    def lint(
        self, root: SkillsRoot, category: str | None = None
    ) -> LintReport:
        """Run the full lint over *root*; optionally filter by *category*.

        The lint combines the 13-rule validator (per-skill, category,
        placement, and duplicate checks) with the weed report (duplicate
        skill names, duplicate descriptions, empty categories, missing
        category descriptions). The result is a single ``LintReport``
        carrying both the issues and the weed lines.
        """
        ...


class ISkillsRunnerProtocol(ABC):
    """Runner capability: run/pause/resume lifecycle verbs."""

    @abstractmethod
    def apply_automatic_transitions(
        self, root: SkillsRoot | None = None
    ) -> MutationOutcome:
        """Apply automatic lifecycle transitions across the pack."""
        ...

    @abstractmethod
    def pause(self, root: SkillsRoot) -> MutationOutcome:
        """Pause lifecycle transitions."""
        ...

    @abstractmethod
    def resume(self, root: SkillsRoot) -> MutationOutcome:
        """Resume lifecycle transitions."""
        ...


__all__ = [
    "ISkillsAdopterProtocol",
    "ISkillsCreatorProtocol",
    "ISkillsLinterProtocol",
    "ISkillsRunnerProtocol",
]

_layer_symbols = {
    "ISkillsAdopterProtocol": ISkillsAdopterProtocol,
    "ISkillsCreatorProtocol": ISkillsCreatorProtocol,
    "ISkillsLinterProtocol": ISkillsLinterProtocol,
    "ISkillsRunnerProtocol": ISkillsRunnerProtocol,
}
