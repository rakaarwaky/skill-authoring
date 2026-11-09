"""Skills-design shared kernel — observability layer.

Logging setup, colors, banners, and structured log helpers plus the
trace-domain contract, taxonomy, and value objects for the skills feature.
"""

from shared.src.observability.contract_traces_aggregate import (
    ISkillsTracesAggregate,
    ISkillsTracesProtocol,
)
from shared.src.observability.taxonomy_traces_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.observability.taxonomy_traces_response import (
    SkillsExitCode,
    SkillsResult,
)
from shared.src.observability.taxonomy_traces_vo import (
    GrokHome,
    PhraseRow,
    PhrasesReport,
    ScanResult,
    TraceRunDir,
    TraceSessionRecord,
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
    "RED",
    "RESET",
    "GrokHome",
    "ISkillsTracesAggregate",
    "ISkillsTracesProtocol",
    "PhraseRow",
    "PhrasesReport",
    "ScanResult",
    "SkillQuery",
    "SkillsExitCode",
    "SkillsOp",
    "SkillsRequest",
    "SkillsResult",
    "SkillsRoot",
    "TraceRunDir",
    "TraceSessionRecord",
    "banner",
    "err",
    "info",
]
