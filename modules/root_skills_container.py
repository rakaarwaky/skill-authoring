"""Skills-design root container (AES composition root).

Wires the four module-side agents (design, discovery, storage,
maintenance) into a single composed aggregate.

The composed agent routes each ``SkillsOp`` to its owning module agent;
the CLI surface receives one ``ISkillsAggregate`` (the composed facade),
injected at the call site, so no root→surface coupling exists.

Discovery ops are translated at the boundary: ``SkillsRequest`` →
``DiscoveryRequest`` on the way in, ``DiscoveryResponse`` →
``SkillsResult`` on the way out.
"""

from __future__ import annotations

# AES402/E402: flat intra-module imports (e.g. ``from agent_design_orchestrator``)
# resolve only when each module's ``src/`` is on sys.path; the composition root
# puts them there before importing module containers (regression on CI runner,
# PYTHONPATH differs from a developer checkout).
import sys as _sys
from pathlib import Path as _Path

_MODULES_ROOT = _Path(__file__).resolve().parent
for _m in (
    "design",
    "discovery",
    "maintenance",
    "shared",
    "cli",
    "storage",
):
    _src = _MODULES_ROOT / _m / "src"
    if _src.is_dir():
        _p = str(_src)
        if _p not in _sys.path:
            _sys.path.append(_p)
if str(_MODULES_ROOT) not in _sys.path:
    _sys.path.append(str(_MODULES_ROOT))


from pathlib import Path

from design.src.root_design_container import create_design_feature
from discovery.src.root_discovery_container import create_discovery_feature
from maintenance.src.root_maintenance_container import (
    create_maintenance_feature,
)
from shared.src.common.utility_common_skills import default_pack_root
from shared.src.design.contract_design_aggregate import ISkillsAggregate
from shared.src.design.contract_design_protocol import (
    ISkillsCreatorProtocol,
    ISkillsLinterProtocol,
)
from shared.src.design.taxonomy_design_request import (
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
from shared.src.maintenance.contract_maintenance_protocol import (
    ISkillsMoverProtocol,
)
from shared.src.maintenance.taxonomy_maintenance_request import (
    MaintenanceRequest,
    MaintenanceVerb,
)
from shared.src.maintenance.taxonomy_maintenance_response import (
    MaintenanceResponse,
)
from shared.src.storage.contract_storage_protocol import ISkillsArchiverProtocol
from shared.src.storage.taxonomy_storage_request import (
    StorageRequest,
    StorageVerb,
)
from shared.src.storage.taxonomy_storage_response import StorageResponse
from storage.src.capabilities_skills_restore import SkillsRestore
from storage.src.root_storage_container import create_storage_feature

__all__ = [
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
    restore: SkillsRestore | None = None,
    default_root: Path | None = None,
) -> ISkillsAggregate:
    """Return a composed agent bound to the repo's ``skills/`` pack."""
    root = default_root if default_root is not None else default_pack_root()

    design = create_design_feature(
        root=root,
        creator=creator,
        linter=linter,
    )
    discovery = create_discovery_feature(
        root=root,
        catalog=catalog,
        discover=discover,
        lister=lister,
        reader=reader,
    )
    maintenance = create_maintenance_feature(
        root=root,
        mover=mover,
    )
    storage = create_storage_feature(
        root=root,
        archiver=archiver,
        restore=restore,
    )

    return _ComposedAggregate(
        design=design,
        discovery=discovery,
        maintenance=maintenance,
        storage=storage,
    )


class _ComposedAggregate(ISkillsAggregate):
    def __init__(
        self,
        design,
        discovery,
        maintenance,
        storage,
    ) -> None:
        self._design = design
        self._discovery = discovery
        self._maintenance = maintenance
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
        elif op in _MAINTENANCE_OPS:
            mreq = MaintenanceRequest(
                verb=MaintenanceVerb(op.value),
                skill=request.query,
                root=request.root,
                flags=request.flags,
            )
            mresp = self._maintenance.execute(mreq)
            result = _maintenance_response_to_result(mresp, op)
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
        return result


def _discovery_response_to_result(
    dresp: DiscoveryResponse, op: SkillsOp
) -> SkillsResult:
    matches = ()
    warning = dresp.warning
    if dresp.discovery is not None:
        matches = dresp.discovery.matches
        if dresp.discovery.warning and not warning:
            warning = dresp.discovery.warning
    return SkillsResult(
        ok=dresp.ok,
        op=op,
        exit_code=dresp.exit_code,
        message=dresp.message,
        records=dresp.records,
        content=dresp.content,
        catalog=dresp.catalog_report,
        check=dresp.catalog_check,
        catalog_text=dresp.catalog_text,
        matches=matches,
        warning=warning,
        root=dresp.root,
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
        dry_run=mresp.dry_run,
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
        content=sresp.content,
    )


_DESIGN_OPS = frozenset(
    {
        SkillsOp.CREATE,
        SkillsOp.LINT,
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
_MAINTENANCE_OPS = frozenset(
    {
        SkillsOp.PRUNE,
        SkillsOp.MOVE,
        SkillsOp.PIN,
        SkillsOp.UNPIN,
        SkillsOp.USAGE,
        SkillsOp.STATUS,
    }
)
_STORAGE_OPS = frozenset(
    {
        SkillsOp.ARCHIVE,
        SkillsOp.EXPORT,
        SkillsOp.RESTORE,
    }
)