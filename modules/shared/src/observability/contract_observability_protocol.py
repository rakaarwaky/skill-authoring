"""Observability-domain capability contracts (AES contract layer, ABC traits).

One seam per observability-side capability: traces, telemetry.
Capabilities implement these; the composition root injects them into
the agent. No import of sibling domain contracts — observability keeps
its own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.common.taxonomy_common_vo import (
    SkillName,
    SkillsRoot,
)
from shared.src.design.taxonomy_design_vo import TelemetryRow
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
    ) -> ScanResult:
        """Walk ``$GROK_HOME/sessions`` and return a compact scan outcome.

        A hardcoded monthly (30-day) window is used; no day window override,
        minimum-turn filter, limit, or watermark is exposed.
        """
        ...

    @abstractmethod
    def build_phrases(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
    ) -> PhrasesReport:
        """Mine repeated exact prompts and repeated instruction lines."""
        ...


class ISkillsPhraseProtocol(ABC):
    """Mine repeated phrases from session records and write ``phrase.json``."""

    @abstractmethod
    def build_phrases(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
    ) -> PhrasesReport:
        """Read session records from ``run_dir``; write ``phrase.json``; return report."""
        ...


class ISkillsUsageProtocol(ABC):
    """Compute per-skill usage analytics from session records and write ``usage.json``."""

    @abstractmethod
    def write_usage(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        records: tuple[TraceSessionRecord, ...],
    ) -> list[dict]:
        """Compute per-skill usage analytics; write ``usage.json``; return items."""
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
    def record_use(self, skill: SkillName, root: SkillsRoot) -> None:
        """Bump the used_count counter for *skill*."""
        ...


__all__ = [
    "ISkillsPhraseProtocol",
    "ISkillsTelemetryProtocol",
    "ISkillsTracesProtocol",
    "ISkillsUsageProtocol",
]

_layer_symbols = {
    "ISkillsPhraseProtocol": ISkillsPhraseProtocol,
    "ISkillsTelemetryProtocol": ISkillsTelemetryProtocol,
    "ISkillsTracesProtocol": ISkillsTracesProtocol,
    "ISkillsUsageProtocol": ISkillsUsageProtocol,
    "GROK_HOME_ENV": GROK_HOME_ENV,
    "MIN_SESSIONS_DEFAULT": MIN_SESSIONS_DEFAULT,
    "MIN_TURNS_DEFAULT": MIN_TURNS_DEFAULT,
    "GrokHomeMissingError": GrokHomeMissingError,
    "NoSessionsError": NoSessionsError,
    "ObservabilityError": ObservabilityError,
}
