"""Storage-domain capability contracts (AES contract layer, ABC traits).

One seam per storage-side capability: archiver, exporter, restore.
Capabilities implement these; the composition root injects them into
the agent. No import of sibling domain contracts — storage keeps its
own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from shared.src.common.taxonomy_common_vo import (
    MutationOutcome,
    MutationPlan,
    SkillName,
)
from shared.src.storage.taxonomy_storage_request import SkillsRoot


class ISkillsArchiverProtocol(ABC):
    """Archive capability: plan/apply an archive of a skill into ``_archive/``."""

    @abstractmethod
    def plan_archive(self, skill: SkillName, root: SkillsRoot) -> MutationPlan:
        """Resolve an archive into ``_archive/`` (pure; no writes)."""
        ...

    @abstractmethod
    def apply_archive(self, plan: MutationPlan) -> MutationOutcome:
        """Execute an archive plan; re-checks containment first."""
        ...


class ISkillsExportProtocol(ABC):
    """Export capability: export a skill folder to a single Markdown file."""

    @abstractmethod
    def export(self, skill: SkillName, root: SkillsRoot | None = None) -> Path:
        ...


class ISkillsRestoreProtocol(ABC):
    """Restore capability: archive / restore verbs."""

    @abstractmethod
    def archive(self, skill: SkillName, root: SkillsRoot | None = None) -> MutationOutcome:
        ...

    @abstractmethod
    def restore(self, skill: SkillName, root: SkillsRoot | None = None) -> MutationOutcome:
        ...


__all__ = [
    "ISkillsArchiverProtocol",
    "ISkillsExportProtocol",
    "ISkillsRestoreProtocol",
]

_layer_symbols = {
    "ISkillsArchiverProtocol": ISkillsArchiverProtocol,
    "ISkillsExportProtocol": ISkillsExportProtocol,
    "ISkillsRestoreProtocol": ISkillsRestoreProtocol,
}