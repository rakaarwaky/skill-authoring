"""Storage-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the storage-side capabilities:
archiver, backup, restore, rollback.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.storage.contract_storage_protocol import (
    ISkillsArchiverProtocol,
    ISkillsBackupProtocol,
    ISkillsRestoreProtocol,
    ISkillsRollbackProtocol,
)
from shared.src.storage.taxonomy_storage_request import StorageRequest
from shared.src.storage.taxonomy_storage_response import StorageResponse

__all__ = [
    "ISkillsArchiverProtocol",
    "ISkillsBackupProtocol",
    "ISkillsRestoreProtocol",
    "ISkillsRollbackProtocol",
    "ISkillsStorageAggregate",
]


class ISkillsStorageAggregate(ABC):
    """Single entry point over storage-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: StorageRequest) -> StorageResponse:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
