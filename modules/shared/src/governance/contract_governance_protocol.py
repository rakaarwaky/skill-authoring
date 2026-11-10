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

from shared.src.common.taxonomy_common_vo import (
    MutationOutcome,
    MutationPlan,
    SkillName,
)
from shared.src.governance.taxonomy_governance_entity import LockState, PinState
from shared.src.governance.taxonomy_governance_error import (
    GovernanceError,
    SkillAlreadyLockedError,
    SkillAlreadyPinnedError,
    SkillNotLockedError,
    SkillNotPinnedError,
)


class ISkillsLockerProtocol(ABC):
    """Locker capability: lock/unlock verbs."""

    @abstractmethod
    def lock(self, skill: SkillName, root: Path | None = None) -> dict:
        ...

    @abstractmethod
    def unlock(self, skill: SkillName, root: Path | None = None) -> dict:
        ...


class ISkillsPinerProtocol(ABC):
    """Piner capability: pin/unpin verbs."""

    @abstractmethod
    def pin(self, skill: SkillName, root: Path | None = None) -> dict:
        ...

    @abstractmethod
    def unpin(self, skill: SkillName, root: Path | None = None) -> dict:
        ...


class ISkillsMoverProtocol(ABC):
    """Mover capability: move a skill between categories."""

    @abstractmethod
    def plan_move(
        self, skill: SkillName, target: str, root: Path | None = None
    ) -> MutationPlan:
        """Resolve a move to another category (pure; no writes)."""
        ...

    @abstractmethod
    def apply_move(self, plan: MutationPlan) -> MutationOutcome:
        """Execute a move plan; re-checks containment first."""
        ...


__all__ = [
    "ISkillsLockerProtocol",
    "ISkillsMoverProtocol",
    "ISkillsPinerProtocol",
]

_layer_symbols = {
    "ISkillsLockerProtocol": ISkillsLockerProtocol,
    "ISkillsMoverProtocol": ISkillsMoverProtocol,
    "ISkillsPinerProtocol": ISkillsPinerProtocol,
    "GovernanceError": GovernanceError,
    "SkillAlreadyLockedError": SkillAlreadyLockedError,
    "SkillAlreadyPinnedError": SkillAlreadyPinnedError,
    "SkillNotLockedError": SkillNotLockedError,
    "SkillNotPinnedError": SkillNotPinnedError,
    "LockState": LockState,
    "PinState": PinState,
}
