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
from shared.src.governance.taxonomy_governance_entity import LockState, PinState
from shared.src.governance.taxonomy_governance_error import GovernanceError
from shared.src.governance.taxonomy_governance_request import GovernanceRequest
from shared.src.governance.taxonomy_governance_response import GovernanceResponse

#: Lock states the locker/piner capabilities manage (re-exported for discovery).
GOVERNANCE_LOCK_STATES = (LOCK_STATE_ACTIVE, LOCK_STATE_LOCKED)
#: Pin states the piner capability manages (re-exported for discovery).
GOVERNANCE_PIN_STATES = (PIN_STATE_UNPINNED, PIN_STATE_PINNED)
#: Sidecar file holding lock/pin state per skill (re-exported for discovery).
GOVERNANCE_LOCK_STATE_FILE = LOCK_STATE_FILENAME
#: Entity types the governance aggregate produces (re-exported for discovery).
GOVERNANCE_ENTITIES = (LockState, PinState)
#: Base error the governance aggregate may raise (re-exported for discovery).
GOVERNANCE_ERROR_BASE = GovernanceError

__all__ = [
    "GOVERNANCE_ERROR_BASE",
    "GOVERNANCE_ENTITIES",
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
