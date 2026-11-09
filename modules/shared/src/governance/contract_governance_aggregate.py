"""Governance-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the governance-side capabilities:
locker, piner, mover.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.design.taxonomy_design_request import SkillsRequest
from shared.src.design.taxonomy_design_response import SkillsResult
from shared.src.governance.contract_governance_protocol import (
    ISkillsLockerProtocol,
    ISkillsMoverProtocol,
    ISkillsPinerProtocol,
)

__all__ = [
    "ISkillsGovernanceAggregate",
    "ISkillsLockerProtocol",
    "ISkillsMoverProtocol",
    "ISkillsPinerProtocol",
]


class ISkillsGovernanceAggregate(ABC):
    """Single entry point over governance-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
