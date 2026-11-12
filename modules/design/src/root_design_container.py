"""Design composition root (AES root layer).

Wires the design-side capabilities (creator, adopter, linter, runner)
into the design orchestrator and exposes the ``ISkillsDesignAggregate``
contract to the surface and entry layers.

Wiring only: no business logic, no orchestration policy, no technical
parsing, no UI behaviour — those live in capabilities / agent / surface.
"""

from __future__ import annotations

from pathlib import Path

from agent_design_orchestrator import SkillsDesignAgent
from capabilities_skills_adopter import SkillsAdopter
from capabilities_skills_creator import SkillsCreator
from capabilities_skills_linter import SkillsLinter
from capabilities_skills_runner import SkillsRunner
from shared.src.common.utility_common_skills import default_pack_root
from shared.src.design.contract_design_aggregate import ISkillsDesignAggregate

__all__ = [
    "DesignContainer",
    "create_design_feature",
]


class DesignContainer:
    """Construct the four capabilities and the design orchestrator (wiring only)."""

    def __init__(
        self,
        adopter: SkillsAdopter | None = None,
        creator: SkillsCreator | None = None,
        linter: SkillsLinter | None = None,
        runner: SkillsRunner | None = None,
        default_root: Path | None = None,
    ) -> None:
        root = default_root if default_root is not None else default_pack_root()
        self._adopter = adopter or SkillsAdopter()
        self._creator = creator or SkillsCreator()
        self._linter = linter or SkillsLinter()
        self._runner = runner or SkillsRunner()
        self._orchestrator = SkillsDesignAgent(
            adopter=self._adopter,
            creator=self._creator,
            linter=self._linter,
            runner=self._runner,
            default_root=root,
        )

    @property
    def aggregate(self) -> ISkillsDesignAggregate:
        """Expose the design aggregate contract, never a concrete orchestrator."""
        return self._orchestrator


def create_design_feature(
    root: Path | None = None,
    *,
    adopter: SkillsAdopter | None = None,
    creator: SkillsCreator | None = None,
    linter: SkillsLinter | None = None,
    runner: SkillsRunner | None = None,
) -> ISkillsDesignAggregate:
    """Fully-wired design feature aggregate (factory for entry / DI).

    ``root`` overrides the default pack root; individual capability overrides
    are for DI / test injection.
    """
    return DesignContainer(
        adopter=adopter,
        creator=creator,
        linter=linter,
        runner=runner,
        default_root=root,
    ).aggregate
