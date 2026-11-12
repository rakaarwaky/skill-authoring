"""Observability-domain response value objects (AES taxonomy layer).

The typed response envelope: ``ObservabilityResult`` is what the surface
renders after one observability op. Payload fields are populated per op
and never re-read from a capability.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING

from shared.src.observability.taxonomy_observability_request import (
    ObservabilityOp,
)

if TYPE_CHECKING:
    from shared.src.observability.taxonomy_observability_entity import (
        ScanResult,
    )
    from shared.src.observability.taxonomy_observability_vo import (
        PhraseRow,
    )


class ObservabilityExitCode(IntEnum):
    """Single source of truth for the CLI exit-code contract."""

    CLEAN = 0
    ISSUES_FOUND = 1
    USAGE_ERROR = 2
    CATALOG_DRIFT = 3


@dataclass(frozen=True)
class ObservabilityResult:
    """Response to an observability operation.

    ``exit_code`` is the CLI contract: 0 clean / 1 issues / 2 usage /
    3 catalog drift. Payload fields are populated per op; the surface
    renders them and never reaches back into a capability.
    """

    ok: bool
    op: ObservabilityOp = ObservabilityOp.PHRASES
    exit_code: int = 0
    message: str = ""
    root: Path | None = None
    phrases_exact: tuple[PhraseRow, ...] = ()
    phrases_stems: tuple[PhraseRow, ...] = ()
    phrases_lines: tuple[PhraseRow, ...] = ()
    scan_summary: ScanResult | None = None


__all__ = ["ObservabilityExitCode", "ObservabilityResult"]

_layer_symbols = {
    "ObservabilityExitCode": ObservabilityExitCode,
    "ObservabilityResult": ObservabilityResult,
}
