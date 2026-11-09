"""Governance-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the governance-side capabilities:
locker, piner, mover.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.governance.contract_governance_protocol import (
    ISkillsLockerProtocol,
    ISkillsMoverProtocol,
    ISkillsPinerProtocol,
)
from shared.src.governance.taxonomy_governance_entity import LockState, PinState
from shared.src.governance.taxonomy_governance_error import (
    GovernanceError,
    SkillAlreadyLockedError,
    SkillAlreadyPinnedError,
    SkillNotLockedError,
    SkillNotPinnedError,
)
from shared.src.governance.taxonomy_governance_request import GovernanceRequest
from shared.src.governance.taxonomy_governance_response import GovernanceResponse

__all__ = [
    "GovernanceError",
    "ISkillsGovernanceAggregate",
    "ISkillsLockerProtocol",
    "ISkillsMoverProtocol",
    "ISkillsPinerProtocol",
    "LockState",
    "PinState",
    "SkillAlreadyLockedError",
    "SkillAlreadyPinnedError",
    "SkillNotLockedError",
    "SkillNotPinnedError",
]


class ISkillsGovernanceAggregate(ABC):
    """Single entry point over governance-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: GovernanceRequest) -> GovernanceResponse:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
