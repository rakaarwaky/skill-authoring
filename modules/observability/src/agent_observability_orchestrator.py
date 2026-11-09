"""Observability agent (AES agent layer).

Implements ``ISkillsObservabilityAggregate`` over the observability-side capabilities:
ledger, telemetry. Owns the ops: ledger, usage.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from shared.src.common.taxonomy_common_error import (
    SkillsError,
    SkillsRootError,
)
from shared.src.observability.contract_observability_aggregate import (
    ISkillsObservabilityAggregate,
)
from shared.src.observability.contract_observability_protocol import (
    ISkillsLedgerProtocol,
    ISkillsTelemetryProtocol,
)
from shared.src.observability.taxonomy_observability_request import (
    ObservabilityRequest,
    ObservabilityOp,
    SkillsRoot,
)
from shared.src.observability.taxonomy_observability_response import (
    ObservabilityExitCode,
    ObservabilityResult,
)

__all__ = [
    "ISkillsObservabilityAggregate",
    "SkillsObservabilityAgent",
]


class SkillsObservabilityAgent(ISkillsObservabilityAggregate):
    """Observability-side agent: ledger / usage."""

    def __init__(
        self,
        ledger: ISkillsLedgerProtocol | None = None,
        telemetry: ISkillsTelemetryProtocol | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._ledger = ledger
        self._telemetry = telemetry
        self._default_root = default_root

    # ─── Block 1: Module Declaration ────────────────────────────────────────
    def _require(self, capability: object, name: str) -> object:
        if capability is None:
            raise SkillsRootError(f"observability capability not wired: {name}")
        return capability

    def _root(self, request: ObservabilityRequest) -> SkillsRoot | None:
        if request.root:
            return request.root
        return self._default_root

    # ─── Block 2: Module Contract ────────────────
    def execute(self, request: ObservabilityRequest) -> ObservabilityResult:
        """Route *request* to the matching observability capability."""
        try:
            op = ObservabilityOp(request.op)
        except ValueError:
            return ObservabilityResult(
                ok=False,
                op=ObservabilityOp.PHRASES,
                exit_code=ObservabilityExitCode.USAGE_ERROR,
                message=f"Unknown observability op: {request.op}",
            )

        try:
            handler = self._handler_for(op)
        except KeyError:
            return ObservabilityResult(
                ok=False,
                op=op,
                exit_code=ObservabilityExitCode.USAGE_ERROR,
                message=f"Unknown observability op: {op}",
            )

        try:
            return handler(request, op)
        except SkillsError as failure:
            return ObservabilityResult(
                ok=False,
                op=op,
                exit_code=failure.exit_code,
                message=str(failure),
            )

    def _handler_for(
        self, op: ObservabilityOp
    ) -> Callable[[ObservabilityRequest, ObservabilityOp], ObservabilityResult]:
        name = f"_execute_{op.value}"
        handler = getattr(self, name, None)
        if not callable(handler):
            raise KeyError(name)
        return cast(Callable[[ObservabilityRequest, ObservabilityOp], ObservabilityResult], handler)

    # ─── Block 3: Module Helpers ────────────────────────────────
    def _execute_ledger(self, request: ObservabilityRequest, op: ObservabilityOp) -> ObservabilityResult:
        """LEDGER: append an entry to the audit ledger."""
        ledger = self._require(self._ledger, "ledger")
        root = self._root(request)
        entry = {
            "action": str(request.flags.get("action", "patch")),
            "skill": str(request.query or ""),
            "before": request.flags.get("before", []),
            "after": request.flags.get("after", []),
            "evidence": request.flags.get("evidence", {}),
        }
        try:
            result = ledger.ledger_append(root, entry)
        except OSError as failure:
            return ObservabilityResult(
                ok=False,
                op=op,
                exit_code=ObservabilityExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return ObservabilityResult(ok=True, op=op, message=str(result))

    def _execute_usage(self, request: ObservabilityRequest, op: ObservabilityOp) -> ObservabilityResult:
        """USAGE: bump/report per-skill telemetry sidecar."""
        telemetry = self._require(self._telemetry, "telemetry")
        root = self._root(request)
        verb = request.flags.get("verb", "report")
        skill = str(request.query or "")
        if verb == "seed":
            telemetry.seed_record_if_missing(skill, root)
            return ObservabilityResult(ok=True, op=op, message=f"seeded {skill}")
        if verb == "reanchor":
            telemetry.reanchor_clock(skill, root)
            return ObservabilityResult(ok=True, op=op, message=f"reanchored {skill}")
        report = telemetry.curated_report(root)
        return ObservabilityResult(ok=True, op=op, records=report, root=root)

    def record_view(self, skill: str, root: SkillsRoot | None = None) -> None:
        """Public seam: bump the ``views`` counter for *skill* in ``.usage.json``."""
        telemetry = self._require(self._telemetry, "telemetry")
        target_root = root if root is not None else self._root(
            ObservabilityRequest(op=ObservabilityOp.USAGE, query=skill)
        )
        telemetry.view(skill, target_root)
