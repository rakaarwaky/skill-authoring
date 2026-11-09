"""Observability-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the observability-side capabilities:
ledger, telemetry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.observability.contract_observability_protocol import (
    ISkillsLedgerProtocol,
    ISkillsTelemetryProtocol,
)
from shared.src.observability.taxonomy_observability_request import (
    ObservabilityRequest,
)
from shared.src.observability.taxonomy_observability_response import (
    ObservabilityResult,
)

__all__ = [
    "ISkillsLedgerProtocol",
    "ISkillsObservabilityAggregate",
    "ISkillsTelemetryProtocol",
]


class ISkillsObservabilityAggregate(ABC):
    """Single entry point over observability-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: ObservabilityRequest) -> ObservabilityResult:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
