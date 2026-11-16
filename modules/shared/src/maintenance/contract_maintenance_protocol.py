"""Maintenance-domain capability contracts (AES contract layer, ABC traits).

One seam per maintenance-side capability: prune, runner, piner, mover.
The prune capability owns both archive-idle and purge-old-archive passes;
the runner capability owns lifecycle transitions and pause/resume; the
piner toggles the pinned flag; the mover plans and applies cross-category
moves. The composition root injects them into the agent. No import of
sibling domain contracts — maintenance keeps its own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.common.taxonomy_common_vo import (
    MutationOutcome,
    MutationPlan,
    SkillName,
)
from shared.src.maintenance.taxonomy_maintenance_entity import PinState
from shared.src.maintenance.taxonomy_maintenance_constant import (
    MAINTENANCE_LOCK_FILENAME,
    MAINTENANCE_SIDECAR_FILENAME,
    PRUNE_TTL_DEFAULT_DAYS,
    PURGE_TTL_DEFAULT_DAYS,
)
from shared.src.maintenance.taxonomy_maintenance_request import SkillsRoot
from shared.src.maintenance.taxonomy_maintenance_response import (
    MaintenanceResponse,
)


class ISkillsPrunerProtocol(ABC):
    """Prune capability: archive idle skills, then purge old archives."""

    @abstractmethod
    def prune(
        self,
        root: SkillsRoot | None = None,
        days: int | None = None,
        purge_days: int | None = None,
        dry_run: bool = False,
    ) -> MaintenanceResponse:
        """Archive idle skills past *days*; purge archived skills past *purge_days*."""
        ...


class ISkillsRunnerProtocol(ABC):
    """Runner capability: run/pause/resume lifecycle verbs."""

    @abstractmethod
    def apply_automatic_transitions(
        self, root: SkillsRoot | None = None
    ) -> MutationOutcome:
        """Apply automatic lifecycle transitions across the pack."""
        ...

    @abstractmethod
    def pause(self, root: SkillsRoot) -> MutationOutcome:
        """Pause lifecycle transitions."""
        ...

    @abstractmethod
    def resume(self, root: SkillsRoot) -> MutationOutcome:
        """Resume lifecycle transitions."""
        ...


class ISkillsPinerProtocol(ABC):
    """Piner capability: pin/unpin verbs."""

    @abstractmethod
    def pin(self, skill: SkillName, root: SkillsRoot | None = None) -> PinState:
        ...

    @abstractmethod
    def unpin(self, skill: SkillName, root: SkillsRoot | None = None) -> PinState:
        ...


class ISkillsMoverProtocol(ABC):
    """Mover capability: move a skill between categories."""

    @abstractmethod
    def plan_move(
        self, skill: SkillName, target: SkillName, root: SkillsRoot
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
    "ISkillsPrunerProtocol",
    "ISkillsRunnerProtocol",
]

_layer_symbols = {
    "ISkillsMoverProtocol": ISkillsMoverProtocol,
    "ISkillsPinerProtocol": ISkillsPinerProtocol,
    "ISkillsPrunerProtocol": ISkillsPrunerProtocol,
    "ISkillsRunnerProtocol": ISkillsRunnerProtocol,
    "MAINTENANCE_LOCK_FILENAME": MAINTENANCE_LOCK_FILENAME,
    "MAINTENANCE_SIDECAR_FILENAME": MAINTENANCE_SIDECAR_FILENAME,
    "PRUNE_TTL_DEFAULT_DAYS": PRUNE_TTL_DEFAULT_DAYS,
    "PURGE_TTL_DEFAULT_DAYS": PURGE_TTL_DEFAULT_DAYS,
}