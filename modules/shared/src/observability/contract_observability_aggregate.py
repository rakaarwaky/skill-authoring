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
from shared.src.observability.taxonomy_observability_request import ObservabilityOp
from shared.src.observability.taxonomy_observability_response import ObservabilityExitCode

#: Operations the observability aggregate exposes (re-exported for discovery).
OBSERVABILITY_OPS = (ObservabilityOp.PHRASES, ObservabilityOp.SCAN)
#: Exit codes the observability aggregate reports (re-exported for discovery).
OBSERVABILITY_EXIT_CODES = (
    ObservabilityExitCode.CLEAN,
    ObservabilityExitCode.ISSUES_FOUND,
    ObservabilityExitCode.USAGE_ERROR,
    ObservabilityExitCode.CATALOG_DRIFT,
)
#: Env var naming the Grok home where session traces live (re-exported).
OBSERVABILITY_GROK_HOME_ENV = GROK_HOME_ENV
#: Minimum sessions for phrase reporting (re-exported).
OBSERVABILITY_MIN_SESSIONS_DEFAULT = MIN_SESSIONS_DEFAULT
#: Minimum turns per session for scan inclusion (re-exported).
OBSERVABILITY_MIN_TURNS_DEFAULT = MIN_TURNS_DEFAULT
#: Base observability error (re-exported for discovery).
OBSERVABILITY_ERROR_BASE = ObservabilityError

__all__ = [
    "ISkillsLedgerProtocol",
    "IObservabilityAggregate",
    "ISkillsTelemetryProtocol",
    "ISkillsTracesProtocol",
    "OBSERVABILITY_ERROR_BASE",
    "OBSERVABILITY_EXIT_CODES",
    "OBSERVABILITY_GROK_HOME_ENV",
    "OBSERVABILITY_MIN_SESSIONS_DEFAULT",
    "OBSERVABILITY_MIN_TURNS_DEFAULT",
    "OBSERVABILITY_OPS",
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
