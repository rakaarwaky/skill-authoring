"""Storage-domain capability contracts (AES contract layer, ABC traits).

One seam per storage-side capability: bootstrap, archiver, backup,
restore, rollback. Capabilities implement these;
the composition root injects them into the agent. No import of
sibling domain contracts — storage keeps its own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from shared.src.common.taxonomy_common_vo import (
    EntryId,
    SkillName,
)
from shared.src.design.taxonomy_design_vo import (
    MutationOutcome,
    MutationPlan,
)
from shared.src.storage.taxonomy_storage_request import SkillsRoot, StorageVerb
from shared.src.storage.taxonomy_storage_response import StorageResponse


class ISkillsBootstrapProtocol(ABC):
    """Bootstrap capability: initialize a skill pack root."""

    @abstractmethod
    def bootstrap(self, root: SkillsRoot | None = None) -> StorageResponse:
        ...


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


class ISkillsBackupProtocol(ABC):
    """Backup capability: snapshot create / prune."""

    @abstractmethod
    def create_snapshot(self, root: SkillsRoot | None = None, *, _prune: bool = True) -> Path:
        ...

    @abstractmethod
    def prune_old_snapshots(
        self, root: SkillsRoot | None = None, *, excluded: frozenset[str] | None = None
    ) -> list[Path]:
        ...

    @abstractmethod
    def resolve_root(self, root: SkillsRoot | Path) -> Path:
        """Validate and return the pack root, raising ``SkillsRootError``."""
        ...

    @abstractmethod
    def backup_root(self, skills_root: Path) -> Path:
        """Return (creating if needed) the snapshot directory under *skills_root*."""
        ...


class ISkillsRestoreProtocol(ABC):
    """Restore capability: archive / restore verbs."""

    @abstractmethod
    def archive(self, skill: SkillName, root: SkillsRoot | None = None) -> MutationOutcome:
        ...

    @abstractmethod
    def restore(self, skill: SkillName, root: SkillsRoot | None = None) -> MutationOutcome:
        ...


class ISkillsRollbackProtocol(ABC):
    """Rollback capability: restore pack from snapshot."""

    @abstractmethod
    def rollback(self, root: SkillsRoot | Path, id_: EntryId | None = None) -> MutationOutcome:
        ...


__all__ = [
    "ISkillsArchiverProtocol",
    "ISkillsBackupProtocol",
    "ISkillsBootstrapProtocol",
    "ISkillsRestoreProtocol",
    "ISkillsRollbackProtocol",
]

_layer_symbols = {
    "ISkillsArchiverProtocol": ISkillsArchiverProtocol,
    "ISkillsBackupProtocol": ISkillsBackupProtocol,
    "ISkillsBootstrapProtocol": ISkillsBootstrapProtocol,
    "ISkillsRestoreProtocol": ISkillsRestoreProtocol,
    "ISkillsRollbackProtocol": ISkillsRollbackProtocol,
}
