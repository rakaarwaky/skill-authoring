"""Governance-domain capability contracts (AES contract layer, ABC traits).

One seam per governance-side capability: locker, piner, mover.
Capabilities implement these; the composition root injects them into
the agent. No import of sibling domain protocols — governance keeps
its own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from shared.src.common.taxonomy_common_vo import SkillName
from shared.src.governance.taxonomy_governance_request import GovernanceRequest
from shared.src.governance.taxonomy_governance_response import GovernanceResponse


class ISkillsLockerProtocol(ABC):
    """Locker capability: lock/unlock verbs."""

    @abstractmethod
    def lock(self, skill: SkillName, root: Path | None = None) -> GovernanceResponse:
        ...

    @abstractmethod
    def unlock(self, skill: SkillName, root: Path | None = None) -> GovernanceResponse:
        ...


class ISkillsPinerProtocol(ABC):
    """Piner capability: pin/unpin verbs."""

    @abstractmethod
    def pin(self, skill: SkillName, root: Path | None = None) -> GovernanceResponse:
        ...

    @abstractmethod
    def unpin(self, skill: SkillName, root: Path | None = None) -> GovernanceResponse:
        ...


class ISkillsMoverProtocol(ABC):
    """Mover capability: move a skill between categories."""

    @abstractmethod
    def move(
        self,
        skill: SkillName,
        target_category: SkillName,
        root: Path | None = None,
    ) -> GovernanceResponse:
        ...


class ISkillsGovernanceAggregate(ABC):
    """Single entry point over governance-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: GovernanceRequest) -> GovernanceResponse:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...


__all__ = [
    "ISkillsGovernanceAggregate",
    "ISkillsLockerProtocol",
    "ISkillsMoverProtocol",
    "ISkillsPinerProtocol",
]

_layer_symbols = {
    "ISkillsGovernanceAggregate": ISkillsGovernanceAggregate,
    "ISkillsLockerProtocol": ISkillsLockerProtocol,
    "ISkillsMoverProtocol": ISkillsMoverProtocol,
    "ISkillsPinerProtocol": ISkillsPinerProtocol,
}
