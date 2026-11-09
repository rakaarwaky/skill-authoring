"""Governance agent (AES agent layer).

Implements ``ISkillsGovernanceAggregate`` over the governance-side capabilities:
locker, piner, mover. Owns the ops: lock, unlock, pin, unpin, move.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from shared.src.common.taxonomy_common_error import (
    SkillsError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.governance.contract_governance_aggregate import (
    ISkillsGovernanceAggregate,
)
from shared.src.governance.contract_governance_protocol import (
    ISkillsLockerProtocol,
    ISkillsMoverProtocol,
    ISkillsPinerProtocol,
)
from shared.src.governance.taxonomy_governance_request import (
    GovernanceRequest,
    GovernanceVerb,
    SkillsRoot,
)
from shared.src.governance.taxonomy_governance_response import GovernanceResponse

__all__ = [
    "ISkillsGovernanceAggregate",
    "SkillsGovernanceAgent",
]

EXIT_USAGE = 2
EXIT_ISSUES_FOUND = 1


class SkillsGovernanceAgent(ISkillsGovernanceAggregate):
    """Governance-side agent: lock / unlock / pin / unpin / move."""

    def __init__(
        self,
        locker: ISkillsLockerProtocol | None = None,
        piner: ISkillsPinerProtocol | None = None,
        mover: ISkillsMoverProtocol | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._locker = locker
        self._piner = piner
        self._mover = mover
        self._default_root = default_root

    # ─── Block 1: Module Declaration ────────────────────────────────────────
    def _require(self, capability: object, name: str) -> object:
        if capability is None:
            raise SkillsRootError(f"governance capability not wired: {name}")
        return capability

    def _root(self, request: GovernanceRequest) -> SkillsRoot | None:
        if request.root:
            return request.root
        return self._default_root

    def _mutate_skill(
        self,
        request: GovernanceRequest,
        op: GovernanceVerb,
        capability: object,
        verb: str,
        field: str,
        value: object,
    ) -> GovernanceResponse:
        root = self._root(request)
        if not request.query or str(request.query).strip() in ("", "None"):
            return GovernanceResponse(
                ok=False,
                verb=op.value,
                exit_code=EXIT_ISSUES_FOUND,
                message="Skill name required",
            )
        skill_name = str(request.query).strip()
        try:
            result = getattr(capability, verb)(skill_name, root)
        except (OSError, ValueError, SkillsUsageError) as failure:
            return GovernanceResponse(
                ok=False,
                verb=op.value,
                exit_code=EXIT_ISSUES_FOUND,
                message=str(failure),
            )
        return GovernanceResponse(ok=True, verb=op.value, message=str(result))

    # ─── Block 2: Module Contract ────────────────────────────────────────
    def execute(self, request: GovernanceRequest) -> GovernanceResponse:
        """Route *request* to the matching governance capability."""
        try:
            op = GovernanceVerb(request.verb)
        except ValueError:
            return GovernanceResponse(
                ok=False,
                verb=GovernanceVerb.LOCK.value,
                exit_code=EXIT_USAGE,
                message=f"Unknown governance op: {request.verb}",
            )

        try:
            handler = self._handler_for(op)
        except KeyError:
            return GovernanceResponse(
                ok=False,
                verb=op.value,
                exit_code=EXIT_USAGE,
                message=f"Unknown governance op: {op}",
            )

        try:
            return handler(request, op)
        except SkillsError as failure:
            return GovernanceResponse(
                ok=False,
                verb=op.value,
                exit_code=failure.exit_code,
                message=str(failure),
            )

    def _handler_for(
        self, op: GovernanceVerb
    ) -> Callable[[GovernanceRequest, GovernanceVerb], GovernanceResponse]:
        name = f"_execute_{op.value}"
        handler = getattr(self, name, None)
        if not callable(handler):
            raise KeyError(name)
        return cast(Callable[[GovernanceRequest, GovernanceVerb], GovernanceResponse], handler)

    # ─── Block 3: Module Helpers ────────────────────────────────────────
    def _execute_move(self, request: GovernanceRequest, op: GovernanceVerb) -> GovernanceResponse:
        """MOVE: plan/apply a skill to another category."""
        mover = self._require(self._mover, "mover")
        root = self._root(request)
        if not request.query or str(request.query).strip() in ("", "None"):
            return GovernanceResponse(
                ok=False,
                verb=op.value,
                exit_code=EXIT_ISSUES_FOUND,
                message="Skill name required",
            )
        skill_name = str(request.query).strip()
        target = request.flags.get("target") or request.flags.get("category")
        if not target:
            raise SkillsUsageError("Missing --target: pass --target <category>")
        apply_ = request.flags.get("apply", False) == "1" or request.flags.get("apply") is True
        plan = mover.plan_move(skill_name, target, root)
        if apply_:
            outcome = mover.apply_move(plan)
            return GovernanceResponse(
                ok=True,
                verb=op.value,
                plan=plan,
                outcome=outcome,
                root=root,
                message=str(outcome.message),
            )
        return GovernanceResponse(
            ok=True,
            verb=op.value,
            plan=plan,
            root=root,
            message=str(plan.kind),
        )

    def _execute_lock(self, request: GovernanceRequest, op: GovernanceVerb) -> GovernanceResponse:
        """LOCK: set locked=True on skill sidecar."""
        locker = self._require(self._locker, "locker")
        return self._mutate_skill(request, op, locker, "lock", "locked", True)

    def _execute_unlock(self, request: GovernanceRequest, op: GovernanceVerb) -> GovernanceResponse:
        """UNLOCK: set locked=False on skill sidecar."""
        locker = self._require(self._locker, "locker")
        return self._mutate_skill(request, op, locker, "unlock", "locked", False)

    def _execute_pin(self, request: GovernanceRequest, op: GovernanceVerb) -> GovernanceResponse:
        """PIN: set pinned=True on skill sidecar."""
        piner = self._require(self._piner, "piner")
        return self._mutate_skill(request, op, piner, "pin", "pinned", True)

    def _execute_unpin(self, request: GovernanceRequest, op: GovernanceVerb) -> GovernanceResponse:
        """UNPIN: set pinned=False on skill sidecar."""
        piner = self._require(self._piner, "piner")
        return self._mutate_skill(request, op, piner, "unpin", "pinned", False)

    def show_skill(self, name: str, root: SkillsRoot | None = None) -> GovernanceResponse:
        """Governance agent does not expose show_skill."""
        return GovernanceResponse(
            ok=False,
            verb=GovernanceVerb.LOCK.value,
            exit_code=EXIT_USAGE,
            message=f"governance agent does not expose show_skill for {name}",
        )
