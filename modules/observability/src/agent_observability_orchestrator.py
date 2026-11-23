"""Observability agent (AES agent layer).

Merges ``SkillsObservabilityAgent`` (telemetry) and
``SkillsPhraseAgent`` (traces / phrase scan) into a single
``ObservabilityAgent`` implementing ``IObservabilityAggregate``.
Owns the ops: usage, traces/phrases.
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from typing import cast

from shared.src.common.taxonomy_common_error import (
    SkillsError,
    SkillsRootError,
)
from shared.src.design.taxonomy_design_request import (
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.design.taxonomy_design_response import (
    SkillsExitCode,
    SkillsResult,
)
from shared.src.observability.contract_observability_aggregate import (
    IObservabilityAggregate,
)
from shared.src.observability.contract_observability_protocol import (
    ISkillsMemoryProtocol,
    ISkillsPhraseProtocol,
    ISkillsTelemetryProtocol,
    ISkillsTracesProtocol,
    ISkillsUsageProtocol,
)

__all__ = ["IObservabilityAggregate", "ObservabilityAgent"]


class ObservabilityAgent(IObservabilityAggregate):
    """Merged observability agent: usage / traces.

    Dispatches ``SkillsOp.USAGE`` to the telemetry capability,
    and ``SkillsOp.TRACES`` to the phrase-scan capability.
    """

    def __init__(
        self,
        telemetry: ISkillsTelemetryProtocol | None = None,
        scan: ISkillsTracesProtocol | None = None,
        usage: ISkillsUsageProtocol | None = None,
        phrase: ISkillsPhraseProtocol | None = None,
        memory: ISkillsMemoryProtocol | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._telemetry = telemetry
        self._scan = scan
        self._usage = usage
        self._phrase = phrase
        self._memory = memory
        self._default_root = default_root

    # ─── Block 1: Module Declaration ────────────────────────────────────────
    def _require(self, capability: object, name: str) -> object:
        if capability is None:
            raise SkillsRootError(f"observability capability not wired: {name}")
        return capability

    def _root(self, request: SkillsRequest) -> SkillsRoot | None:
        if request.root:
            return request.root
        return self._default_root

    # ─── Block 2: Module Contract ────────────────
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching observability capability."""
        try:
            op = SkillsOp(request.op)
        except ValueError:
            return SkillsResult(
                ok=False,
                op=SkillsOp.USAGE,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown observability op: {request.op}",
            )

        try:
            handler = self._handler_for(op)
        except KeyError:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown observability op: {op}",
            )

        try:
            return handler(request, op)
        except SkillsError as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=failure.exit_code,
                message=str(failure),
            )

    def _handler_for(
        self, op: SkillsOp
    ) -> Callable[[SkillsRequest, SkillsOp], SkillsResult]:
        name = f"_execute_{op.value.replace('-', '_')}"
        handler = getattr(self, name, None)
        if not callable(handler):
            raise KeyError(name)
        return cast(Callable[[SkillsRequest, SkillsOp], SkillsResult], handler)

    # ─── Block 3: Module Helpers ────────────────────────────────
    def _execute_usage(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """USAGE: bump/report per-skill telemetry sidecar."""
        telemetry = self._require(self._telemetry, "telemetry")
        root = self._root(request)
        verb = request.flags.get("verb", "report")
        skill = str(request.query or "")
        if verb == "seed":
            telemetry.seed_record_if_missing(skill, root)
            return SkillsResult(ok=True, op=op, message=f"seeded {skill}")
        if verb == "reanchor":
            telemetry.reanchor_clock(skill, root)
            return SkillsResult(ok=True, op=op, message=f"reanchored {skill}")
        report = telemetry.curated_report(root)
        return SkillsResult(ok=True, op=op, records=report, root=root)

    def _execute_status(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """STATUS: inspect lifecycle state for all skills in the pack."""
        telemetry = self._require(self._telemetry, "telemetry")
        root = self._root(request)
        report = telemetry.curated_report(root)
        return SkillsResult(
            ok=True,
            op=op,
            exit_code=SkillsExitCode.CLEAN,
            records=report,
            root=root,
        )

    def _execute_traces(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """TRACES: route on ``flags['traces_action']`` ('phrases', 'usage', or 'memory')."""
        traces_action = request.flags.get("traces_action", "")
        if traces_action == "memory":
            return self._execute_memory(request, op)
        if traces_action == "phrases":
            return self._execute_phrases(request, op)
        if traces_action == "usage":
            return self._execute_usage_traces(request, op)
        return SkillsResult(
            ok=False,
            op=op,
            exit_code=SkillsExitCode.USAGE_ERROR,
            message=f"Unknown traces action: {traces_action or '(none)'}",
        )

    def _execute_memory(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """MEMORY: mine repeated signals from memory-v2."""
        memory = self._require(self._memory, "memory")
        grok_home = request.flags.get("grok_home", "")
        run_dir = request.flags.get("run_dir", "") or ""
        if not run_dir:
            run_dir = tempfile.mkdtemp(prefix="sac-memory-")
            request.flags["run_dir"] = run_dir

        report = memory.scan_memory(grok_home, run_dir)

        return SkillsResult(
            ok=True,
            op=op,
            exit_code=SkillsExitCode.CLEAN,
            message=f"Memory mined → {run_dir}/memory.json",
            memory=report,
            root=self._root(request),
        )

    def _execute_phrases(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """PHRASES: mine repeated prompts from session records."""
        phrase = self._require(self._phrase, "phrase")
        grok_home = request.flags.get("grok_home", "")
        run_dir = request.flags.get("run_dir", "") or ""
        if not run_dir:
            run_dir = tempfile.mkdtemp(prefix="sac-phrases-")
            request.flags["run_dir"] = run_dir

        # Scan sessions first (builds session records in run_dir).
        scan = self._require(self._scan, "scan")
        scan_result = scan.scan_sessions(
            grok_home,
            run_dir,
        )

        # Mine repeated phrases from the records written to run_dir.
        report = phrase.build_phrases(grok_home, run_dir)

        return SkillsResult(
            ok=True,
            op=op,
            exit_code=SkillsExitCode.CLEAN,
            message=f"Phrases mined → {run_dir}/phrases.json",
            phrases_exact=report.exact_prompts,
            phrases_stems=report.stems,
            phrases_lines=report.repeated_instruction_lines,
            scan_summary=scan_result,
            root=self._root(request),
        )

    def _execute_usage_traces(
        self, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """USAGE (traces): scan sessions and fold usage analytics into sidecar.

        Scans sessions only (no build_phrases), writes usage.json via
        ``self._usage.write_usage``, then folds used_count into the
        ``.usage.json`` sidecar via ``self._telemetry.fold_used_count_into_sidecar``.
        No direct sidecar write in the agent.
        """
        scan = self._require(self._scan, "scan")
        grok_home = request.flags.get("grok_home", "")
        run_dir = request.flags.get("run_dir", "") or ""
        if not run_dir:
            run_dir = tempfile.mkdtemp(prefix="sac-usage-")
            request.flags["run_dir"] = run_dir

        scan_result = scan.scan_sessions(grok_home, run_dir)
        records = scan_result.records

        usage = self._require(self._usage, "usage")
        usage.write_usage(grok_home, run_dir, records)

        telemetry = self._require(self._telemetry, "telemetry")
        telemetry.fold_used_count_into_sidecar(grok_home, run_dir, records)

        return SkillsResult(
            ok=True,
            op=op,
            exit_code=SkillsExitCode.CLEAN,
            message=f"Usage scanned → {run_dir}/usage.json",
            scan_summary=scan_result,
            root=self._root(request),
        )

    def record_use(self, skill: str, root: SkillsRoot | None = None) -> None:
        """Public seam: bump the ``used_count`` counter for *skill* in ``.usage.json``."""
        telemetry = self._require(self._telemetry, "telemetry")
        target_root = (
            root
            if root is not None
            else self._root(SkillsRequest(op=SkillsOp.USAGE, query=skill))
        )
        telemetry.record_use(skill, target_root)
