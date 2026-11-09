"""Governance-domain entities (AES taxonomy layer).

Identity-bearing domain records produced by the locker/piner/mover
capabilities. Pure data: no I/O, no imports from utility, capabilities,
agent, root, or surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.src.common.taxonomy_common_vo import SkillName
from shared.src.governance.taxonomy_governance_constant import LOCK_STATE_ACTIVE


@dataclass(frozen=True)
class LockState:
    """The lock state of a single skill."""

    skill: SkillName
    state: str = LOCK_STATE_ACTIVE
    locked_at: str | None = None


@dataclass(frozen=True)
class PinState:
    """The pin state of a single skill."""

    skill: SkillName
    pinned: bool = False
    pinned_at: str | None = None


__all__ = ["LockState", "PinState"]

_layer_symbols = {
    "LockState": LockState,
    "PinState": PinState,
}
