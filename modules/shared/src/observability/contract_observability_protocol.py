"""Observability-domain capability contracts (AES contract layer, ABC traits).

One seam per observability-side capability: traces, ledger, telemetry.
Capabilities implement these; the composition root injects them into
the agent. No import of sibling domain contracts — observability keeps
its own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from shared.src.common.taxonomy_common_vo import EntryId, SkillName
from shared.src.common.taxonomy_common_vo import SkillsRoot
from shared.src.design.taxonomy_design_vo import (
    LedgerEntry,
    MutationOutcome,
    TelemetryRow,
)
from shared.src.observability.taxonomy_observability_constant import (
    GROK_HOME_ENV,
    MIN_SESSIONS_DEFAULT,
    MIN_TURNS_DEFAULT,
)
from shared.src.observability.taxonomy_observability_entity import ScanResult
from shared.src.observability.taxonomy_observability_error import (
    GrokHomeMissingError,
    NoSessionsError,
    ObservabilityError,
)
from shared.src.observability.taxonomy_observability_vo import (
    GrokHome,
    PhrasesReport,
    TraceRunDir,
)


class ISkillsTracesProtocol(ABC):
    """Scan sessions and mine repeated phrases."""

    @abstractmethod
    def scan_sessions(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        days: int = 0,
        since_last: bool = False,
        min_turns: int = 1,
        limit: int = 0,
    ) -> ScanResult:
        """Walk ``$GROK_HOME/sessions`` and return a compact scan outcome."""
        ...

    @abstractmethod
    def build_phrases(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        min_sessions: int = 2,
    ) -> PhrasesReport:
        """Mine repeated exact prompts and repeated instruction lines."""
        ...


class ISkillsLedgerProtocol(ABC):
    """Ledger capability: append / read / compact / rollback."""

    @abstractmethod
    def ledger_append(
        self, root: SkillsRoot | Path, entry: LedgerEntry
    ) -> LedgerEntry:
        """Append *entry* to the audit ledger; return the stored entry."""
        ...

    @abstractmethod
    def ledger_read(
        self,
        root: SkillsRoot | Path,
        limit: int | None = None,
    ) -> tuple[LedgerEntry, ...]:
        """Read up to *limit* most recent ledger entries."""
        ...

    @abstractmethod
    def ledger_compact(
        self,
        root: SkillsRoot | Path,
        older_than_days: int | None = None,
        keep_recent: int = 0,
    ) -> MutationOutcome:
        """Compact the ledger beyond *older_than_days*, keeping *keep_recent*."""
        ...

    @abstractmethod
    def rollback_entry(self, root: SkillsRoot | Path, entry_id: EntryId) -> MutationOutcome:
        """Roll back to the state at *entry_id*; return the result."""
        ...


class ISkillsTelemetryProtocol(ABC):
    """Telemetry capability: usage tracking and status reports."""

    @abstractmethod
    def seed_record_if_missing(self, skill: SkillName, root: SkillsRoot) -> None:
        """Seed a baseline telemetry record for *skill* if none exists."""
        ...

    @abstractmethod
    def reanchor_clock(self, skill: SkillName, root: SkillsRoot) -> None:
        """Reset *skill*'s activity timestamps to now."""
        ...

    @abstractmethod
    def curated_report(self, root: SkillsRoot) -> tuple[TelemetryRow, ...]:
        """Return one telemetry row per skill, sorted by name."""
        ...

    @abstractmethod
    def view(self, skill: SkillName, root: SkillsRoot) -> None:
        """Bump the views counter for *skill*."""
        ...


__all__ = [
    "ISkillsLedgerProtocol",
    "ISkillsTelemetryProtocol",
    "ISkillsTracesProtocol",
]

_layer_symbols = {
    "ISkillsLedgerProtocol": ISkillsLedgerProtocol,
    "ISkillsTelemetryProtocol": ISkillsTelemetryProtocol,
    "ISkillsTracesProtocol": ISkillsTracesProtocol,
}
