"""Storage agent (AES agent layer).

Implements ``ISkillsStorageAggregate`` over the storage-side capabilities:
archiver, backup, restore, rollback. Owns the ops: archive, restore,
backup, rollback.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from shared.src.common.taxonomy_common_constant import (
    EXIT_ISSUES_FOUND,
    EXIT_USAGE,
)
from shared.src.common.taxonomy_common_error import (
    SkillsError,
    SkillsRootError,
)
from shared.src.storage.contract_storage_aggregate import (
    ISkillsStorageAggregate,
)
from shared.src.storage.contract_storage_protocol import (
    ISkillsArchiverProtocol,
    ISkillsBackupProtocol,
    ISkillsRestoreProtocol,
    ISkillsRollbackProtocol,
)
from shared.src.storage.taxonomy_storage_request import (
    SkillsRoot,
    StorageRequest,
    StorageVerb,
)
from shared.src.storage.taxonomy_storage_response import StorageResponse

__all__ = [
    "ISkillsStorageAggregate",
    "SkillsStorageAgent",
]


class SkillsStorageAgent(ISkillsStorageAggregate):
    """Storage-side agent: archive / restore / backup / rollback."""

    def __init__(
        self,
        archiver: ISkillsArchiverProtocol | None = None,
        backup: ISkillsBackupProtocol | None = None,
        restore: ISkillsRestoreProtocol | None = None,
        rollback: ISkillsRollbackProtocol | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._archiver = archiver
        self._backup = backup
        self._restore = restore
        self._rollback = rollback
        self._default_root = default_root

    # ─── Block 1: Module Declaration ────────────────────────────────────────
    def _require(self, capability: object, name: str) -> object:
        if capability is None:
            raise SkillsRootError(f"storage capability not wired: {name}")
        return capability

    def _root(self, request: StorageRequest) -> SkillsRoot | None:
        if request.root:
            return request.root
        return self._default_root

    # ─── Block 2: Module Contract ────────────────
    def execute(self, request: StorageRequest) -> StorageResponse:
        """Route *request* to the matching storage capability."""
        try:
            op = StorageVerb(request.verb)
        except ValueError:
            return StorageResponse(
                ok=False,
                verb=StorageVerb.BOOTSTRAP.value,
                exit_code=EXIT_USAGE,
                message=f"Unknown storage op: {request.verb}",
            )

        try:
            handler = self._handler_for(op)
        except KeyError:
            return StorageResponse(
                ok=False,
                verb=op.value,
                exit_code=EXIT_USAGE,
                message=f"Unknown storage op: {op}",
            )

        try:
            return handler(request, op)
        except SkillsError as failure:
            return StorageResponse(
                ok=False,
                verb=op.value,
                exit_code=failure.exit_code,
                message=str(failure),
            )

    def _handler_for(
        self, op: StorageVerb
    ) -> Callable[[StorageRequest, StorageVerb], StorageResponse]:
        name = f"_execute_{op.value}"
        handler = getattr(self, name, None)
        if not callable(handler):
            raise KeyError(name)
        return cast(Callable[[StorageRequest, StorageVerb], StorageResponse], handler)

    # ─── Block 3: Module Helpers ────────────────────────────────
    def _execute_archive(self, request: StorageRequest, op: StorageVerb) -> StorageResponse:
        """ARCHIVE: move a live skill into _archive/."""
        archiver = self._require(self._archiver, "archiver")
        root = self._root(request)
        if not request.query or str(request.query).strip() in ("", "None"):
            return StorageResponse(
                ok=False,
                verb=op.value,
                exit_code=EXIT_ISSUES_FOUND,
                message="Skill name required",
            )
        skill_name = str(request.query).strip()
        try:
            result = archiver.archive(skill_name, root)
        except (OSError, SkillsError) as failure:
            return StorageResponse(
                ok=False,
                verb=op.value,
                exit_code=EXIT_ISSUES_FOUND,
                message=str(failure),
            )
        return StorageResponse(ok=True, verb=op.value, message=str(result))

    def _execute_restore(self, request: StorageRequest, op: StorageVerb) -> StorageResponse:
        """RESTORE: restore an archived skill back to the live pack."""
        restore = self._require(self._restore, "restore")
        root = self._root(request)
        if not request.query or str(request.query).strip() in ("", "None"):
            return StorageResponse(
                ok=False,
                verb=op.value,
                exit_code=EXIT_ISSUES_FOUND,
                message="Skill name required",
            )
        skill_name = str(request.query).strip()
        try:
            result = restore.restore(skill_name, root)
        except (OSError, SkillsError) as failure:
            return StorageResponse(
                ok=False,
                verb=op.value,
                exit_code=EXIT_ISSUES_FOUND,
                message=str(failure),
            )
        return StorageResponse(ok=True, verb=op.value, message=str(result))

    def _execute_backup(self, request: StorageRequest, op: StorageVerb) -> StorageResponse:
        """BACKUP: create a content-addressed snapshot of the pack."""
        backup = self._require(self._backup, "backup")
        root = self._root(request)
        try:
            path = backup.create_snapshot(root)
        except OSError as failure:
            return StorageResponse(
                ok=False,
                verb=op.value,
                exit_code=EXIT_ISSUES_FOUND,
                message=str(failure),
            )
        return StorageResponse(ok=True, verb=op.value, message=str(path), root=root)

    def _execute_rollback(self, request: StorageRequest, op: StorageVerb) -> StorageResponse:
        """ROLLBACK: restore the pack tree from a stored snapshot."""
        rollback = self._require(self._rollback, "rollback")
        root = self._root(request)
        snapshot_id = request.flags.get("id") or request.query
        try:
            result = rollback.rollback(root, snapshot_id)
        except OSError as failure:
            return StorageResponse(
                ok=False,
                verb=op.value,
                exit_code=EXIT_ISSUES_FOUND,
                message=str(failure),
            )
        return StorageResponse(ok=True, verb=op.value, message=str(result))
