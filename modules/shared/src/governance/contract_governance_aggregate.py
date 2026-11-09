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
from shared.src.governance.taxonomy_governance_constant import (
    LOCK_STATE_ACTIVE,
    LOCK_STATE_FILENAME,
    LOCK_STATE_LOCKED,
    PIN_STATE_PINNED,
    PIN_STATE_UNPINNED,
)
from shared.src.governance.taxonomy_governance_request import GovernanceRequest
from shared.src.governance.taxonomy_governance_response import GovernanceResponse

#: Lock states the locker/piner capabilities manage (re-exported for discovery).
GOVERNANCE_LOCK_STATES = (LOCK_STATE_ACTIVE, LOCK_STATE_LOCKED)
#: Pin states the piner capability manages (re-exported for discovery).
GOVERNANCE_PIN_STATES = (PIN_STATE_UNPINNED, PIN_STATE_PINNED)
#: Sidecar file holding lock/pin state per skill (re-exported for discovery).
GOVERNANCE_LOCK_STATE_FILE = LOCK_STATE_FILENAME

__all__ = [
    "ISkillsGovernanceAggregate",
    "ISkillsLockerProtocol",
    "ISkillsMoverProtocol",
    "ISkillsPinerProtocol",
    "LOCK_STATE_ACTIVE",
    "LOCK_STATE_FILENAME",
    "LOCK_STATE_LOCKED",
    "PIN_STATE_PINNED",
    "PIN_STATE_UNPINNED",
    "GOVERNANCE_LOCK_STATES",
    "GOVERNANCE_PIN_STATES",
    "GOVERNANCE_LOCK_STATE_FILE",
]


class ISkillsGovernanceAggregate(ABC):
    """Single entry point over governance-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: GovernanceRequest) -> GovernanceResponse:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
