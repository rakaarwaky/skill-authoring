"""Discovery composition root (AES root layer).

Wires the discovery-side capabilities (catalog, discover, lister, reader)
into the discovery orchestrator and exposes the ``ISkillsDiscoveryAggregate``
contract to the surface and entry layers.

Wiring only: no business logic, no orchestration policy, no technical
parsing, no UI behaviour — those live in capabilities / agent / surface.
"""
from __future__ import annotations

from pathlib import Path

from agent_discovery_orchestrator import SkillsDiscoveryAgent
from capabilities_discovery_catalog import SkillsCatalog
from capabilities_discovery_finder import SkillsDiscover
from capabilities_discovery_lister import SkillsLister
from capabilities_discovery_reader import SkillsPackReader

from shared.src.common.utility_common_skills import default_pack_root
from shared.src.discovery.contract_discovery_aggregate import (
    ISkillsDiscoveryAggregate,
)
from shared.src.discovery.taxonomy_discovery_vo import SkillsBm25fRanker

__all__ = [
    "DiscoveryContainer",
    "create_discovery_feature",
]


class DiscoveryContainer:
    """Construct the four capabilities and the discovery orchestrator (wiring only)."""

    def __init__(
        self,
        catalog: SkillsCatalog | None = None,
        discover: SkillsDiscover | None = None,
        lister: SkillsLister | None = None,
        reader: SkillsPackReader | None = None,
        default_root: Path | None = None,
    ) -> None:
        root = default_root if default_root is not None else default_pack_root()
        self._catalog = catalog or SkillsCatalog()
        self._discover = discover or SkillsDiscover(
            self._catalog, SkillsBm25fRanker()
        )
        self._lister = lister or SkillsLister()
        self._reader = reader or SkillsPackReader()
        self._orchestrator = SkillsDiscoveryAgent(
            catalog=self._catalog,
            discover=self._discover,
            lister=self._lister,
            reader=self._reader,
            default_root=root,
        )

    @property
    def aggregate(self) -> ISkillsDiscoveryAggregate:
        """Expose the discovery aggregate contract, never a concrete orchestrator."""
        return self._orchestrator


def create_discovery_feature(
    root: Path | None = None,
    *,
    catalog: SkillsCatalog | None = None,
    discover: SkillsDiscover | None = None,
    lister: SkillsLister | None = None,
    reader: SkillsPackReader | None = None,
) -> ISkillsDiscoveryAggregate:
    """Fully-wired discovery feature aggregate (factory for entry / DI).

    ``root`` overrides the default pack root; individual capability overrides
    are for DI / test injection.
    """
    return DiscoveryContainer(
        catalog=catalog,
        discover=discover,
        lister=lister,
        reader=reader,
        default_root=root,
    ).aggregate
