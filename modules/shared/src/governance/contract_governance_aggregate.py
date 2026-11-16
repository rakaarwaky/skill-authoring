"""Governance-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the governance-side capabilities:
piner, mover.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.governance.contract_governance_protocol import (
    ISkillsMoverProtocol,
    ISkillsPinerProtocol,
)
from shared.src.governance.taxonomy_governance_constant import (
    PIN_STATE_PINNED,
    PIN_STATE_UNPINNED,
)
from shared.src.governance.taxonomy_governance_request import GovernanceRequest
from shared.src.governance.taxonomy_governance_response import (
    GovernanceResponse,
)

#: Pin states the piner capability manages (re-exported for discovery).
GOVERNANCE_PIN_STATES = (PIN_STATE_UNPINNED, PIN_STATE_PINNED)

__all__ = [
    "GOVERNANCE_PIN_STATES",
    "PIN_STATE_PINNED",
    "PIN_STATE_UNPINNED",
    "ISkillsGovernanceAggregate",
    "ISkillsMoverProtocol",
    "ISkillsPinerProtocol",
]


class ISkillsGovernanceAggregate(ABC):
    """Single entry point over governance-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: GovernanceRequest) -> GovernanceResponse:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
