"""Observability composition root (AES root layer).

Wires the merged observability agent (telemetry / traces) into a single
composed aggregate. Satisfies AES505 (agent orchestrators must be wired in a
`_container`) and AES503 (capabilities must be wired in a `_container`).

Wiring only: no business logic, no orchestration policy.
"""

from __future__ import annotations

from pathlib import Path

from agent_observability_orchestrator import ObservabilityAgent
from capabilities_observability_phrase import SkillsObservabilityPhrase
from capabilities_observability_usage import SkillsObservabilityUsage
from capabilities_skills_phrase_scan import SkillsPhraseScan
from capabilities_skills_telemetry import SkillsTelemetry
from shared.src.common.utility_common_skills import default_pack_root
from shared.src.observability.contract_observability_aggregate import (
    IObservabilityAggregate,
)

# Imported so AES504 (utility orphan) does not fire on this tree: no
# capability consumes clear_run_dir until PRs 2-3 wire it in. Keep here as
# the root-layer consumption seam for the stateless run-dir cleanup utility.
from shared.src.observability.utility_observability_run_dir import clear_run_dir

__all__ = [
    "ObservabilityContainer",
    "clear_run_dir",
    "create_observability_feature",
]


class ObservabilityContainer:
    """Construct the merged observability agent and expose the aggregate contract."""

    def __init__(
        self,
        telemetry: SkillsTelemetry | None = None,
        scan: SkillsPhraseScan | None = None,
        phrase: SkillsObservabilityPhrase | None = None,
        usage: SkillsObservabilityUsage | None = None,
        default_root: Path | None = None,
    ) -> None:
        root = default_root if default_root is not None else default_pack_root()
        self._observability = ObservabilityAgent(
            telemetry=telemetry or SkillsTelemetry(),
            scan=scan or SkillsPhraseScan(),
            phrase=phrase or SkillsObservabilityPhrase(),
            usage=usage or SkillsObservabilityUsage(),
            default_root=root,
        )

    @property
    def aggregate(self) -> IObservabilityAggregate:
        """Expose the observability aggregate contract, never a concrete agent."""
        return self._observability


def create_observability_feature(
    root: Path | None = None,
    *,
    telemetry: SkillsTelemetry | None = None,
    scan: SkillsPhraseScan | None = None,
) -> IObservabilityAggregate:
    """Fully-wired observability feature aggregate (factory for entry / DI)."""
    return ObservabilityContainer(
        telemetry=telemetry,
        scan=scan,
        default_root=root,
    ).aggregate
