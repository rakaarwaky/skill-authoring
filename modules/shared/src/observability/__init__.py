"""Skills-design shared kernel — observability layer.

Logging setup, colors, banners, and structured log helpers plus the
trace-domain contract, taxonomy, and value objects for the skills feature.
"""

from shared.src.observability.contract_observability_aggregate import (
    IObservabilityAggregate,
)
from shared.src.observability.contract_observability_protocol import (
    ISkillsTracesProtocol,
)
from shared.src.observability.taxonomy_observability_constant import (
    GROK_HOME_ENV,
    MIN_SESSIONS_DEFAULT,
    MIN_TURNS_DEFAULT,
)
from shared.src.observability.taxonomy_observability_entity import (
    ScanResult,
    TraceSessionRecord,
)
from shared.src.observability.taxonomy_observability_error import (
    GrokHomeMissingError,
    NoSessionsError,
    ObservabilityError,
)
from shared.src.observability.taxonomy_observability_request import (
    ObservabilityOp,
    ObservabilityRequest,
    SkillQuery,
    SkillsRoot,
)
from shared.src.observability.taxonomy_observability_response import (
    ObservabilityExitCode,
    ObservabilityResult,
)
from shared.src.observability.taxonomy_observability_vo import (
    GrokHome,
    PhraseRow,
    PhrasesReport,
    TraceRunDir,
)
from shared.src.observability.utility_logging_setup import (
    BOLD,
    CYAN,
    DIM,
    RED,
    RESET,
    banner,
    err,
    info,
)

__all__ = [
    "BOLD",
    "CYAN",
    "DIM",
    "GROK_HOME_ENV",
    "MIN_SESSIONS_DEFAULT",
    "MIN_TURNS_DEFAULT",
    "RED",
    "RESET",
    "GrokHome",
    "GrokHomeMissingError",
    "IObservabilityAggregate",
    "ISkillsTracesProtocol",
    "NoSessionsError",
    "ObservabilityError",
    "ObservabilityExitCode",
    "ObservabilityOp",
    "ObservabilityRequest",
    "ObservabilityResult",
    "PhraseRow",
    "PhrasesReport",
    "ScanResult",
    "SkillQuery",
    "SkillsRoot",
    "TraceRunDir",
    "TraceSessionRecord",
    "banner",
    "err",
    "info",
]
