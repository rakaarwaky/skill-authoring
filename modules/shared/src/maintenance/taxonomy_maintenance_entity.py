"""Maintenance-domain entities (AES taxonomy layer).

Identity-bearing domain records produced by prune, purge, archive, and
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


__all__ = ["MaintenanceRecord", "PruneCandidate"]

_layer_symbols = {
    "MaintenanceRecord": MaintenanceRecord,
    "PruneCandidate": PruneCandidate,
}
