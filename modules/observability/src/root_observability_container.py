"""Observability composition root (AES root layer).

Wires the observability-side agents and capabilities into a single
composed aggregate, mirroring the per-member container pattern used by
discovery. This is the wiring point that satisfies AES505 (agent
orchestrators must be wired in a `_container`) and AES503 (capabilities
must be wired in a `_container`).

Wiring only: no business logic, no orchestration policy.
"""

from __future__ import annotations

from pathlib import Path

from agent_observability_orchestrator import SkillsObservabilityAgent
from agent_skills_phrase_orchestrator import SkillsPhraseAgent
from capabilities_skills_ledger import SkillsLedger
from capabilities_skills_phrase_scan import SkillsPhraseScan
from capabilities_skills_telemetry import SkillsTelemetry
from shared.src.observability.contract_observability_aggregate import (
    ISkillsObservabilityAggregate,
)
from shared.src.observability.contract_traces_aggregate import ISkillsTracesAggregate
from shared.src.storage.utility_skill_pack import default_pack_root

__all__ = [
    "ObservabilityContainer",
    "create_observability_feature",
]


class ObservabilityContainer:
    """Construct the observability agents and expose the aggregate contract."""

    def __init__(
        self,
        ledger: SkillsLedger | None = None,
        telemetry: SkillsTelemetry | None = None,
        scan: SkillsPhraseScan | None = None,
        default_root: Path | None = None,
    ) -> None:
        root = default_root if default_root is not None else default_pack_root()
        self._observability = SkillsObservabilityAgent(
            ledger=ledger or SkillsLedger(),
            telemetry=telemetry or SkillsTelemetry(),
            default_root=root,
        )
        self._traces = SkillsPhraseAgent(
            scan=scan or SkillsPhraseScan(),
            default_root=root,
        )

    @property
    def aggregate(self) -> ISkillsObservabilityAggregate:
        """Expose the observability aggregate contract, never a concrete agent."""
        return self._observability

    @property
    def traces(self) -> ISkillsTracesAggregate:
        """Expose the traces agent aggregate contract."""
        return self._traces


def create_observability_feature(
    root: Path | None = None,
    *,
    ledger: SkillsLedger | None = None,
    telemetry: SkillsTelemetry | None = None,
    scan: SkillsPhraseScan | None = None,
) -> ISkillsObservabilityAggregate:
    """Fully-wired observability feature aggregate (factory for entry / DI)."""
    return ObservabilityContainer(
        ledger=ledger,
        telemetry=telemetry,
        scan=scan,
        default_root=root,
    ).aggregate
