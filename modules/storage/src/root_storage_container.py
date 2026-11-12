"""Storage composition root (AES root layer).

Wires the storage-side capabilities (archiver, backup, restore, rollback)
into the storage orchestrator and exposes the ``ISkillsStorageAggregate``
contract to the surface and entry layers.

Wiring only: no business logic, no orchestration policy, no technical
parsing, no UI behaviour — those live in capabilities / agent / surface.
"""

from __future__ import annotations

from pathlib import Path

from agent_storage_orchestrator import SkillsStorageAgent
from capabilities_skills_archiver import SkillsArchiver
from capabilities_skills_backup import SkillsBackup
from capabilities_skills_bootstrap import SkillsBootstrap
from capabilities_skills_restore import SkillsRestore
from capabilities_skills_rollback import SkillsRollback
from shared.src.common.utility_common_skills import default_pack_root
from shared.src.storage.contract_storage_aggregate import (
    ISkillsStorageAggregate,
)

__all__ = [
    "StorageContainer",
    "create_storage_feature",
]


class StorageContainer:
    """Construct the storage capabilities and the storage orchestrator (wiring only)."""

    def __init__(
        self,
        archiver: SkillsArchiver | None = None,
        backup: SkillsBackup | None = None,
        bootstrap: SkillsBootstrap | None = None,
        restore: SkillsRestore | None = None,
        rollback: SkillsRollback | None = None,
        default_root: Path | None = None,
    ) -> None:
        root = default_root if default_root is not None else default_pack_root()
        self._archiver = archiver or SkillsArchiver()
        self._backup = backup or SkillsBackup()
        self._bootstrap = bootstrap or SkillsBootstrap()
        self._restore = restore or SkillsRestore()
        self._rollback = rollback or SkillsRollback(backup=self._backup)
        self._orchestrator = SkillsStorageAgent(
            archiver=self._archiver,
            backup=self._backup,
            restore=self._restore,
            rollback=self._rollback,
            default_root=root,
        )

    @property
    def aggregate(self) -> ISkillsStorageAggregate:
        """Expose the storage aggregate contract, never a concrete orchestrator."""
        return self._orchestrator


def create_storage_feature(
    root: Path | None = None,
    *,
    archiver: SkillsArchiver | None = None,
    backup: SkillsBackup | None = None,
    restore: SkillsRestore | None = None,
    rollback: SkillsRollback | None = None,
) -> ISkillsStorageAggregate:
    """Fully-wired storage feature aggregate (factory for entry / DI).

    ``root`` overrides the default pack root; individual capability overrides
    are for DI / test injection.
    """
    return StorageContainer(
        archiver=archiver,
        backup=backup,
        restore=restore,
        rollback=rollback,
        default_root=root,
    ).aggregate
