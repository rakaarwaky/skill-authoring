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
from shared.src.governance.taxonomy_governance_entity import PinState
from shared.src.governance.taxonomy_governance_error import (
    GovernanceError,
    SkillAlreadyPinnedError,
    SkillNotPinnedError,
)


class ISkillsPinerProtocol(ABC):
    """Piner capability: pin/unpin verbs."""

    @abstractmethod
    def pin(self, skill: SkillName, root: Path | None = None) -> PinState:
        ...

    @abstractmethod
    def unpin(self, skill: SkillName, root: Path | None = None) -> PinState:
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
    "ISkillsMoverProtocol",
    "ISkillsPinerProtocol",
]

_layer_symbols = {
    "ISkillsMoverProtocol": ISkillsMoverProtocol,
    "ISkillsPinerProtocol": ISkillsPinerProtocol,
    "GovernanceError": GovernanceError,
    "SkillAlreadyPinnedError": SkillAlreadyPinnedError,
    "SkillNotPinnedError": SkillNotPinnedError,
    "PinState": PinState,
}
