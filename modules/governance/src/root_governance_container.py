"""Governance composition root (AES root layer).

Wires the governance-side capabilities (locker, piner, mover) into the
governance orchestrator and exposes the ``ISkillsGovernanceAggregate``
contract to the surface and entry layers.

Wiring only: no business logic, no orchestration policy, no technical
parsing, no UI behaviour — those live in capabilities / agent / surface.
"""

from __future__ import annotations

from pathlib import Path

from agent_governance_orchestrator import SkillsGovernanceAgent
from capabilities_skills_locker import SkillsLocker
from capabilities_skills_mover import SkillsMover
from capabilities_skills_piner import SkillsPiner
from shared.src.common.taxonomy_common_utility import default_pack_root
from shared.src.governance.contract_governance_aggregate import (
    ISkillsGovernanceAggregate,
)

__all__ = [
    "GovernanceContainer",
    "create_governance_feature",
]


class GovernanceContainer:
    """Construct the three capabilities and the governance orchestrator (wiring only)."""

    def __init__(
        self,
        locker: SkillsLocker | None = None,
        piner: SkillsPiner | None = None,
        mover: SkillsMover | None = None,
        default_root: Path | None = None,
    ) -> None:
        root = default_root if default_root is not None else default_pack_root()
        self._locker = locker or SkillsLocker()
        self._piner = piner or SkillsPiner()
        self._mover = mover or SkillsMover()
        self._orchestrator = SkillsGovernanceAgent(
            locker=self._locker,
            piner=self._piner,
            mover=self._mover,
            default_root=root,
        )

    @property
    def aggregate(self) -> ISkillsGovernanceAggregate:
        """Expose the governance aggregate contract, never a concrete orchestrator."""
        return self._orchestrator


def create_governance_feature(
    root: Path | None = None,
    *,
    locker: SkillsLocker | None = None,
    piner: SkillsPiner | None = None,
    mover: SkillsMover | None = None,
) -> ISkillsGovernanceAggregate:
    """Fully-wired governance feature aggregate (factory for entry / DI).

    ``root`` overrides the default pack root; individual capability overrides
    are for DI / test injection.
    """
    return GovernanceContainer(
        locker=locker,
        piner=piner,
        mover=mover,
        default_root=root,
    ).aggregate
