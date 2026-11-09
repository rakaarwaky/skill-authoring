"""Storage-domain capability contracts (AES contract layer, ABC traits).

One seam per storage-side capability: bootstrap, lister, reader.
Capabilities implement these; the composition root injects them into
the agent. No import of sibling domain contracts — storage keeps its
own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from shared.src.common.taxonomy_common_vo import SkillContent, SkillName, SkillRecord
from shared.src.storage.taxonomy_storage_request import SkillsRoot, StorageVerb
from shared.src.storage.taxonomy_storage_response import StorageResponse


class ISkillsBootstrapProtocol(ABC):
    """Bootstrap capability: initialize a skill pack root."""

    @abstractmethod
    def bootstrap(self, root: SkillsRoot | None = None) -> StorageResponse:
        ...


class ISkillsListerProtocol(ABC):
    """Read-only listing of the skill pack."""

    @abstractmethod
    def list_skills(self, root: SkillsRoot | None = None) -> Sequence[SkillRecord]:
        ...


class ISkillsReaderProtocol(ABC):
    """Read-only content access to one skill's SKILL.md."""

    @abstractmethod
    def read_skill(self, skill: SkillName, root: SkillsRoot | None = None) -> SkillContent | None:
        ...


class ISkillsStorageAggregate(ABC):
    """Single entry point over storage-side ops."""

    @abstractmethod
    def execute(self, verb: StorageVerb, root: SkillsRoot | None = None) -> StorageResponse:
        """Run the storage operation; return its response."""
        ...


__all__ = [
    "ISkillsBootstrapProtocol",
    "ISkillsListerProtocol",
    "ISkillsReaderProtocol",
    "ISkillsStorageAggregate",
]

_layer_symbols = {
    "ISkillsBootstrapProtocol": ISkillsBootstrapProtocol,
    "ISkillsListerProtocol": ISkillsListerProtocol,
    "ISkillsReaderProtocol": ISkillsReaderProtocol,
    "ISkillsStorageAggregate": ISkillsStorageAggregate,
}
