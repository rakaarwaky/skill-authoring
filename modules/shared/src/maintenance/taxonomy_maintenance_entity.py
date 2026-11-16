"""Maintenance-domain entities (AES taxonomy layer).

Identity-bearing domain records produced by prune, archive, and
restore capabilities. Pure data: no I/O, no imports from utility,
capabilities, agent, root, or surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.src.common.taxonomy_common_vo import SkillName


@dataclass(frozen=True)
class MaintenanceRecord:
    """One maintenance operation record: verb, skill, and outcome."""

    skill: SkillName
    verb: str
    applied: bool
    reason: str = ""


@dataclass(frozen=True)
class PruneCandidate:
    """A skill candidate for pruning: its name and idle age in days."""

    skill: SkillName
    idle_days: int


@dataclass(frozen=True)
class PinState:
    """The pin state of a single skill."""

    skill: SkillName
    pinned: bool = False
    pinned_at: str | None = None


__all__ = ["MaintenanceRecord", "PruneCandidate", "PinState"]

_layer_symbols = {
    "MaintenanceRecord": MaintenanceRecord,
    "PruneCandidate": PruneCandidate,
    "PinState": PinState,
}
