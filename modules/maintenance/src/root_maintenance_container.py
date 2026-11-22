"""Maintenance composition root (AES root layer).

Wires the maintenance-side capabilities (prune, runner, piner, mover)
into the maintenance orchestrator and exposes the
``ISkillsMaintenanceAggregate`` contract to the surface and entry layers.

Wiring only: no business logic, no orchestration policy, no technical
parsing, no UI behaviour — those live in capabilities / agent / surface.
"""

from __future__ import annotations

from pathlib import Path

from agent_maintenance_orchestrator import SkillsMaintenanceAgent
from capabilities_skills_mover import SkillsMover
from capabilities_skills_piner import SkillsPiner
from capabilities_skills_prune import SkillsPrune
from capabilities_skills_runner import SkillsRunner

from shared.src.common.utility_common_skills import default_pack_root
from shared.src.maintenance.contract_maintenance_aggregate import (
    ISkillsMaintenanceAggregate,
)

__all__ = [
    "MaintenanceContainer",
    "create_maintenance_feature",
]


class MaintenanceContainer:
    """Construct the four capabilities and the maintenance orchestrator (wiring only)."""

    def __init__(
        self,
        prune: SkillsPrune | None = None,
        runner: SkillsRunner | None = None,
        piner: SkillsPiner | None = None,
        mover: SkillsMover | None = None,
        default_root: Path | None = None,
    ) -> None:
        root = default_root if default_root is not None else default_pack_root()
        self._prune = prune or SkillsPrune()
        self._runner = runner or SkillsRunner()
        self._piner = piner or SkillsPiner()
        self._mover = mover or SkillsMover()
        self._orchestrator = SkillsMaintenanceAgent(
            prune=self._prune,
            runner=self._runner,
            piner=self._piner,
            mover=self._mover,
            default_root=root,
        )

    @property
    def aggregate(self) -> ISkillsMaintenanceAggregate:
        """Expose the maintenance aggregate contract, never a concrete orchestrator."""
        return self._orchestrator


def create_maintenance_feature(
    root: Path | None = None,
    *,
    prune: SkillsPrune | None = None,
    runner: SkillsRunner | None = None,
    piner: SkillsPiner | None = None,
    mover: SkillsMover | None = None,
) -> ISkillsMaintenanceAggregate:
    """Fully-wired maintenance feature aggregate (factory for entry / DI).

    ``root`` overrides the default pack root; individual capability overrides
    are for DI / test injection.
    """
    return MaintenanceContainer(
        prune=prune,
        runner=runner,
        piner=piner,
        mover=mover,
        default_root=root,
    ).aggregate
