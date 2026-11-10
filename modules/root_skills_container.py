"""Skills-design root container (AES composition root).

Wires the six module-side agents (design, discovery, storage, governance,
maintenance, observability) into a single composed aggregate.

The traces capability of the sibling traces app is NOT imported
here — the two packages are independent (AES702). The composed agent
routes each ``SkillsOp`` to its owning module agent; the CLI surface
receives one ``ISkillsAggregate`` (the composed facade), injected at
the call site, so no root→surface coupling exists.

Discovery ops are translated at the boundary: ``SkillsRequest`` →
``DiscoveryRequest`` on the way in, ``DiscoveryResponse`` →
``SkillsResult`` on the way out.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from design.src.agent_design_orchestrator import SkillsDesignAgent
from design.src.capabilities_skills_adopter import SkillsAdopter
from design.src.capabilities_skills_runner import SkillsRunner
from discovery.src.root_discovery_container import create_discovery_feature
from governance.src.agent_governance_orchestrator import SkillsGovernanceAgent
from governance.src.capabilities_skills_locker import SkillsLocker
from governance.src.capabilities_skills_piner import SkillsPiner
from maintenance.src.agent_maintenance_orchestrator import SkillsMaintenanceAgent
from maintenance.src.capabilities_skills_prune import SkillsPrune
from maintenance.src.capabilities_skills_purge import SkillsPurge
from observability.src.agent_observability_orchestrator import ObservabilityAgent
from observability.src.capabilities_skills_ledger import SkillsLedger
from observability.src.capabilities_skills_phrase_scan import SkillsPhraseScan
from observability.src.capabilities_skills_telemetry import SkillsTelemetry
from shared.src.common.taxonomy_common_vo import (
    SkillRecord,
)
from shared.src.common.utility_common_skills import default_pack_root
from shared.src.design.contract_design_aggregate import ISkillsAggregate
from shared.src.design.contract_design_protocol import (
    ISkillsCreatorProtocol,
    ISkillsLinterProtocol,
)
from shared.src.design.taxonomy_design_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
)
from shared.src.design.taxonomy_design_response import SkillsResult
from shared.src.discovery.contract_discovery_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
    ISkillsListerProtocol,
    ISkillsReaderProtocol,
)
from shared.src.discovery.taxonomy_discovery_request import (
    DiscoveryQuery,
    DiscoveryRequest,
    DiscoveryRoot,
    DiscoveryVerb,
)
from shared.src.discovery.taxonomy_discovery_response import DiscoveryResponse
from shared.src.governance.contract_governance_protocol import ISkillsMoverProtocol
from shared.src.governance.taxonomy_governance_request import (
    GovernanceRequest,
    GovernanceVerb,
)
from shared.src.governance.taxonomy_governance_response import GovernanceResponse
from shared.src.maintenance.taxonomy_maintenance_request import (
    MaintenanceRequest,
    MaintenanceVerb,
)
from shared.src.maintenance.taxonomy_maintenance_response import MaintenanceResponse
from shared.src.storage.contract_storage_protocol import ISkillsArchiverProtocol
from shared.src.storage.taxonomy_storage_request import (
    StorageRequest,
    StorageVerb,
)
from shared.src.storage.taxonomy_storage_response import StorageResponse
from storage.src.agent_storage_orchestrator import SkillsStorageAgent
from storage.src.capabilities_skills_backup import SkillsBackup
from storage.src.capabilities_skills_restore import SkillsRestore
from storage.src.capabilities_skills_rollback import SkillsRollback

__all__ = [
    "SkillsFacade",
    "default_aggregate",
]


def default_aggregate(
    lister: ISkillsListerProtocol | None = None,
    reader: ISkillsReaderProtocol | None = None,
    *,
    linter: ISkillsLinterProtocol | None = None,
    catalog: ISkillsCatalogProtocol | None = None,
    discover: ISkillsDiscoverProtocol | None = None,
    mover: ISkillsMoverProtocol | None = None,
    archiver: ISkillsArchiverProtocol | None = None,
    creator: ISkillsCreatorProtocol | None = None,
    backup: SkillsBackup | None = None,
    restore: SkillsRestore | None = None,
    rollback: SkillsRollback | None = None,
    default_root: Path | None = None,
) -> ISkillsAggregate:
    """Return a composed agent bound to the repo's ``skills/`` pack."""
    root = default_root if default_root is not None else default_pack_root()

    design = SkillsDesignAgent(
        creator=creator,
        adopter=SkillsAdopter(),
        linter=linter,
        runner=SkillsRunner(),
        default_root=root,
    )
    discovery = create_discovery_feature(
        root=root,
        catalog=catalog,
        discover=discover,
        lister=lister,
        reader=reader,
    )
    governance = SkillsGovernanceAgent(
        locker=SkillsLocker(),
        piner=SkillsPiner(),
        mover=mover,
        default_root=root,
    )
    maintenance = SkillsMaintenanceAgent(
        prune=SkillsPrune(),
        purge=SkillsPurge(),
        default_root=root,
    )
    observability = ObservabilityAgent(
        ledger=SkillsLedger(),
        telemetry=SkillsTelemetry(),
        scan=SkillsPhraseScan(),
        default_root=root,
    )
    storage = SkillsStorageAgent(
        archiver=archiver,
        backup=backup or SkillsBackup(),
        restore=restore,
        rollback=rollback or SkillsRollback(backup or SkillsBackup()),
        default_root=root,
    )

    return _ComposedAggregate(
        design=design,
        discovery=discovery,
        governance=governance,
        maintenance=maintenance,
        observability=observability,
        storage=storage,
    )


class _ComposedAggregate(ISkillsAggregate):
    def __init__(
        self,
        design,
        discovery,
        governance,
        maintenance,
        observability,
        storage,
    ) -> None:
        self._design = design
        self._discovery = discovery
        self._governance = governance
        self._maintenance = maintenance
        self._observability = observability
        self._storage = storage

    def execute(self, request: SkillsRequest) -> SkillsResult:
        op = request.op
        if op in _DESIGN_OPS:
            result = self._design.execute(request)
        elif op in _DISCOVERY_OPS:
            dreq = DiscoveryRequest(
                verb=DiscoveryVerb(op.value),
                query=DiscoveryQuery(request.query),
                root=DiscoveryRoot(request.root) if request.root is not None else None,
                flags=request.flags,
            )
            dresp = self._discovery.execute(dreq)
            result = _discovery_response_to_result(dresp, op)
        elif op in _GOVERNANCE_OPS:
            greq = GovernanceRequest(
                verb=GovernanceVerb(op.value),
                query=SkillQuery(request.query),
                root=request.root,
                flags=request.flags,
            )
            gresp = self._governance.execute(greq)
            result = _governance_response_to_result(gresp, op)
        elif op in _MAINTENANCE_OPS:
            mreq = MaintenanceRequest(
                verb=MaintenanceVerb(op.value),
                skill=request.query,
                root=request.root,
                flags=request.flags,
            )
            mresp = self._maintenance.execute(mreq)
            result = _maintenance_response_to_result(mresp, op)
        elif op in _OBSERVABILITY_OPS:
            result = self._observability.execute(request)
        elif op in _STORAGE_OPS:
            sreq = StorageRequest(
                verb=StorageVerb(op.value),
                query=request.query,
                root=request.root,
                flags=request.flags,
            )
            sresp = self._storage.execute(sreq)
            result = _storage_response_to_result(sresp, op)
        else:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=2,
                message=f"Unknown skills op: {op}",
            )
        if result.ok:
            skill_name = str(request.query or "").strip()
            if skill_name:
                self._observability.record_view(skill_name)
        return result


def _discovery_response_to_result(
    dresp: DiscoveryResponse, op: SkillsOp
) -> SkillsResult:
    return SkillsResult(
        ok=dresp.ok,
        op=op,
        exit_code=dresp.exit_code,
        message=dresp.message,
        records=dresp.records,
        content=dresp.content,
        catalog=dresp.catalog_report,
        check=dresp.catalog_check,
        warning=dresp.warning,
        root=dresp.root,
    )


def _governance_response_to_result(
    gresp: GovernanceResponse, op: SkillsOp
) -> SkillsResult:
    return SkillsResult(
        ok=gresp.ok,
        op=op,
        exit_code=gresp.exit_code,
        message=gresp.message,
        root=gresp.root,
        plan=gresp.plan,
        outcome=gresp.outcome,
    )


def _maintenance_response_to_result(
    mresp: MaintenanceResponse, op: SkillsOp
) -> SkillsResult:
    return SkillsResult(
        ok=mresp.ok,
        op=op,
        exit_code=mresp.exit_code,
        message=mresp.message,
        root=mresp.root,
        records=mresp.records,
    )


def _storage_response_to_result(
    sresp: StorageResponse, op: SkillsOp
) -> SkillsResult:
    return SkillsResult(
        ok=sresp.ok,
        op=op,
        exit_code=sresp.exit_code,
        message=sresp.message,
        root=sresp.root,
        records=sresp.records,
        manifest=sresp.manifest,
        content=sresp.content,
    )


_DESIGN_OPS = frozenset(
    {
        SkillsOp.ADOPT,
        SkillsOp.CREATE,
        SkillsOp.LINT,
        SkillsOp.PAUSE,
        SkillsOp.RESUME,
        SkillsOp.RUN,
    }
)
_DISCOVERY_OPS = frozenset(
    {
        SkillsOp.CATALOG,
        SkillsOp.DISCOVER,
        SkillsOp.LINT,
        SkillsOp.LIST,
        SkillsOp.LIST_ARCHIVED,
        SkillsOp.LIST_UNMANAGED,
        SkillsOp.READ,
    }
)
_GOVERNANCE_OPS = frozenset(
    {
        SkillsOp.LOCK,
        SkillsOp.MOVE,
        SkillsOp.PIN,
        SkillsOp.UNLOCK,
        SkillsOp.UNPIN,
    }
)
_MAINTENANCE_OPS = frozenset({SkillsOp.PRUNE, SkillsOp.PURGE})
_OBSERVABILITY_OPS = frozenset({SkillsOp.LEDGER, SkillsOp.USAGE, SkillsOp.TRACES})
_STORAGE_OPS = frozenset(
    {SkillsOp.ARCHIVE, SkillsOp.BACKUP, SkillsOp.RESTORE, SkillsOp.ROLLBACK}
)


class SkillsFacade:
    """Composition root for the skills feature (read + authoring)."""

    def __init__(
        self,
        lister: ISkillsListerProtocol | None = None,
        reader: ISkillsReaderProtocol | None = None,
        *,
        linter: ISkillsLinterProtocol | None = None,
        catalog: ISkillsCatalogProtocol | None = None,
        discover: ISkillsDiscoverProtocol | None = None,
        mover: ISkillsMoverProtocol | None = None,
        archiver: ISkillsArchiverProtocol | None = None,
        creator: ISkillsCreatorProtocol | None = None,
        default_root: Path | None = None,
    ) -> None:
        root = default_root if default_root is not None else default_pack_root()
        self._aggregate = default_aggregate(
            lister=lister,
            reader=reader,
            linter=linter,
            catalog=catalog,
            discover=discover,
            mover=mover,
            archiver=archiver,
            creator=creator,
            default_root=root,
        )

    def execute(self, request: SkillsRequest) -> SkillsResult:
        return self._aggregate.execute(request)

    # ─── Read wrappers ───────────────────────────────────────
    def list_skills(self) -> Sequence[SkillRecord]:
        """Return one record per skill in the pack, sorted by name."""
        from shared.src.design.taxonomy_design_request import SkillsRequest as _SR

        result = self._aggregate.execute(
            _SR(op=SkillsOp.LIST, query=SkillQuery(""), root=None)
        )
        return result.records or []