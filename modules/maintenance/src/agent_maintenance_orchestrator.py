"""Maintenance agent (AES agent layer).

Implements ``ISkillsMaintenanceAggregate`` over the maintenance-side capabilities:
prune, runner, piner, mover. Owns the ops: prune, run, pause, resume,
pin, unpin, move.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from shared.src.common.taxonomy_common_error import (
    SkillsError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.maintenance.contract_maintenance_aggregate import (
    ISkillsMaintenanceAggregate,
)
from shared.src.maintenance.contract_maintenance_protocol import (
    ISkillsMoverProtocol,
    ISkillsPinerProtocol,
    ISkillsPrunerProtocol,
    ISkillsRunnerProtocol,
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
    """Maintenance-side agent: prune, run, pause, resume, pin, unpin, move."""

    def __init__(
        self,
        prune: ISkillsPrunerProtocol | None = None,
        runner: ISkillsRunnerProtocol | None = None,
        piner: ISkillsPinerProtocol | None = None,
        mover: ISkillsMoverProtocol | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._prune = prune
        self._runner = runner
        self._piner = piner
        self._mover = mover
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

    def _execute_run(self, request: MaintenanceRequest, op: MaintenanceVerb) -> MaintenanceResponse:
        """RUN: apply automatic transitions per pass."""
        runner = self._require(self._runner, "runner")
        root = self._root(request)
        try:
            report = runner.apply_automatic_transitions(root)
        except (OSError, ValueError) as failure:
            return MaintenanceResponse(
                ok=False,
                verb=op.value,
                exit_code=1,
                message=str(failure),
            )
        return MaintenanceResponse(ok=True, verb=op.value, message=str(report))

    def _execute_pause(self, request: MaintenanceRequest, op: MaintenanceVerb) -> MaintenanceResponse:
        """PAUSE: set pause=True in config."""
        runner = self._require(self._runner, "runner")
        root = self._root(request)
        try:
            runner.pause(root)
        except (OSError, ValueError) as failure:
            return MaintenanceResponse(
                ok=False,
                verb=op.value,
                exit_code=1,
                message=str(failure),
            )
        return MaintenanceResponse(ok=True, verb=op.value, message="lifecycle paused")

    def _execute_resume(self, request: MaintenanceRequest, op: MaintenanceVerb) -> MaintenanceResponse:
        """RESUME: set pause=False in config."""
        runner = self._require(self._runner, "runner")
        root = self._root(request)
        try:
            runner.resume(root)
        except (OSError, ValueError) as failure:
            return MaintenanceResponse(
                ok=False,
                verb=op.value,
                exit_code=1,
                message=str(failure),
            )
        return MaintenanceResponse(ok=True, verb=op.value, message="lifecycle resumed")

    def _execute_pin(self, request: MaintenanceRequest, op: MaintenanceVerb) -> MaintenanceResponse:
        """PIN: set pinned=True on skill sidecar."""
        piner = self._require(self._piner, "piner")
        root = self._root(request)
        skill_name = str(request.skill or "").strip()
        if not skill_name:
            return MaintenanceResponse(
                ok=False,
                verb=op.value,
                exit_code=1,
                message="Skill name required",
            )
        try:
            result = piner.pin(skill_name, root)
        except (OSError, ValueError, SkillsError) as failure:
            return MaintenanceResponse(
                ok=False,
                verb=op.value,
                exit_code=1,
                message=str(failure),
            )
        return MaintenanceResponse(ok=True, verb=op.value, message=str(result))

    def _execute_unpin(self, request: MaintenanceRequest, op: MaintenanceVerb) -> MaintenanceResponse:
        """UNPIN: set pinned=False on skill sidecar."""
        piner = self._require(self._piner, "piner")
        root = self._root(request)
        skill_name = str(request.skill or "").strip()
        if not skill_name:
            return MaintenanceResponse(
                ok=False,
                verb=op.value,
                exit_code=1,
                message="Skill name required",
            )
        try:
            result = piner.unpin(skill_name, root)
        except (OSError, ValueError, SkillsError) as failure:
            return MaintenanceResponse(
                ok=False,
                verb=op.value,
                exit_code=1,
                message=str(failure),
            )
        return MaintenanceResponse(ok=True, verb=op.value, message=str(result))

    def _execute_move(self, request: MaintenanceRequest, op: MaintenanceVerb) -> MaintenanceResponse:
        """MOVE: plan/apply a move of a skill to another category."""
        mover = self._require(self._mover, "mover")
        root = self._root(request)
        skill_name = str(request.skill or "").strip()
        if not skill_name:
            return MaintenanceResponse(
                ok=False,
                verb=op.value,
                exit_code=1,
                message="Skill name required",
            )
        target = request.flags.get("target") or request.flags.get("category")
        if not target:
            raise SkillsUsageError("Missing --target: pass --target <category>")
        apply_ = request.flags.get("apply", False) == "1" or request.flags.get("apply") is True
        plan = mover.plan_move(skill_name, target, root)
        if apply_:
            outcome = mover.apply_move(plan)
            return MaintenanceResponse(
                ok=True,
                verb=op.value,
                message=str(outcome.message),
            )
        return MaintenanceResponse(
            ok=True,
            verb=op.value,
            message=str(plan.kind),
        )