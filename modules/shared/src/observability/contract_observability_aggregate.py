"""Observability-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the observability-side capabilities:
ledger, telemetry, and traces (phrase scan). The merged
``IObservabilityAggregate`` replaces ``ISkillsObservabilityAggregate``
and ``ISkillsTracesAggregate``; one agent handles ledger, usage, and
traces/phrases ops through the shared ``SkillsRequest``/``SkillsResult``
envelope.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.design.taxonomy_design_request import (
    SkillsRequest,
)
from shared.src.design.taxonomy_design_response import (
    SkillsResult,
)
from shared.src.observability.contract_observability_protocol import (
    ISkillsLedgerProtocol,
    ISkillsTelemetryProtocol,
    ISkillsTracesProtocol,
)
from shared.src.observability.taxonomy_observability_constant import (
    GROK_HOME_ENV,
    MIN_SESSIONS_DEFAULT,
    MIN_TURNS_DEFAULT,
)
from shared.src.observability.taxonomy_observability_error import (
    GrokHomeMissingError,
    NoSessionsError,
    ObservabilityError,
)

__all__ = [
    "GROK_HOME_ENV",
    "ISkillsLedgerProtocol",
    "IObservabilityAggregate",
    "ISkillsTelemetryProtocol",
    "ISkillsTracesProtocol",
    "MIN_SESSIONS_DEFAULT",
    "MIN_TURNS_DEFAULT",
    "NoSessionsError",
    "ObservabilityError",
]


class IObservabilityAggregate(ABC):
    """Single entry point over observability-side ops; the agent dispatches internally.

    Handles ``SkillsOp.LEDGER``, ``SkillsOp.USAGE``, and ``SkillsOp.TRACES``
    through a single ``execute(SkillsRequest) -> SkillsResult`` seam.
    """

    @abstractmethod
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
