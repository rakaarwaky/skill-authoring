"""Maintenance agent (AES agent layer).

Implements ``ISkillsMaintenanceAggregate`` over the maintenance-side capability:
prune. Owns the op: prune.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from shared.src.common.taxonomy_common_error import (
    SkillsError,
    SkillsRootError,
)
from shared.src.common.taxonomy_common_vo import SkillName
from shared.src.maintenance.contract_maintenance_aggregate import (
    ISkillsMaintenanceAggregate,
)
from shared.src.maintenance.contract_maintenance_protocol import (
    ISkillsPrunerProtocol,
)
from shared.src.maintenance.taxonomy_maintenance_request import (
    MaintenanceRequest,
    MaintenanceVerb,
    SkillsRoot,
)
from shared.src.maintenance.taxonomy_maintenance_response import (
    MaintenanceResponse,
)

__all__ = [
    "ISkillsMaintenanceAggregate",
    "SkillsMaintenanceAgent",
]


class SkillsMaintenanceAgent(ISkillsMaintenanceAggregate):
    """Maintenance-side agent: prune."""

    def __init__(
        self,
        prune: ISkillsPrunerProtocol | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._prune = prune
        self._default_root = default_root

    # ─── Block 1: Module Declaration ────────────────────────────────────────
    def _require(self, capability: object, name: str) -> object:
        if capability is None:
            raise SkillsRootError(f"maintenance capability not wired: {name}")
        return capability

    def _root(self, request: MaintenanceRequest) -> SkillsRoot | None:
        if request.root:
            return request.root
        return self._default_root

    # ─── Block 2: Module Contract ────────────────
    def execute(self, request: MaintenanceRequest) -> MaintenanceResponse:
        """Route *request* to the matching maintenance capability."""
        try:
            op = MaintenanceVerb(request.verb)
        except ValueError:
            return MaintenanceResponse(
                ok=False,
                verb=MaintenanceVerb.PRUNE.value,
                exit_code=2,
                message=f"Unknown maintenance op: {request.verb}",
            )

        try:
            handler = self._handler_for(op)
        except KeyError:
            return MaintenanceResponse(
                ok=False,
                verb=op.value,
                exit_code=2,
                message=f"Unknown maintenance op: {op}",
            )

        try:
            return handler(request, op)
        except SkillsError as failure:
            return MaintenanceResponse(
                ok=False,
                verb=op.value,
                exit_code=failure.exit_code,
                message=str(failure),
            )

    def _handler_for(
        self, op: MaintenanceVerb
    ) -> Callable[[MaintenanceRequest, MaintenanceVerb], MaintenanceResponse]:
        name = f"_execute_{op.value}"
        handler = getattr(self, name, None)
        if not callable(handler):
            raise KeyError(name)
        return cast(Callable[[MaintenanceRequest, MaintenanceVerb], MaintenanceResponse], handler)

    # ─── Block 3: Module Helpers ────────────────────────────────
    def _execute_prune(self, request: MaintenanceRequest, op: MaintenanceVerb) -> MaintenanceResponse:
        """PRUNE: archive idle skills, then purge archived skills past their TTL."""
        prune = self._require(self._prune, "prune")
        root = self._root(request)
        days = int(request.flags["days"]) if "days" in request.flags else None
        purge_days = (
            int(request.flags["purge_days"]) if "purge_days" in request.flags else None
        )
        dry_run = bool(
            request.flags.get("dry_run", False) or request.flags.get("dry-run", False)
        )
        try:
            report = prune.prune(
                root=root, days=days, purge_days=purge_days, dry_run=dry_run
            )
        except (OSError, ValueError) as failure:
            return MaintenanceResponse(
                ok=False,
                verb=op.value,
                exit_code=1,
                message=str(failure),
            )
        return MaintenanceResponse(
            ok=True,
            verb=op.value,
            records=report.records,
            message=report.message,
            dry_run=dry_run,
        )