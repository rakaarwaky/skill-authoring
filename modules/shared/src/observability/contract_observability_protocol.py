"""Observability-domain capability contracts (AES contract layer, ABC traits).

One seam per observability-side capability: traces, telemetry, memory.
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
    MemoryReport,
    PhrasesReport,
    TraceRunDir,
)


class ISkillsTracesProtocol(ABC):
    """Scan sessions only (traces capability)."""

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
    """Compute usage analytics, write ``usage.json``, and manage the sidecar."""

    @abstractmethod
    def write_usage(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        records: tuple[TraceSessionRecord, ...],
    ) -> list[dict]:
        """Compute per-skill usage analytics; write ``usage.json``; return items."""
        ...

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

    @abstractmethod
    def fold_used_count_into_sidecar(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        records: tuple[TraceSessionRecord, ...],
    ) -> None:
        """Fold per-skill ``used_count`` analytics into ``.usage.json`` sidecar.

        Reads telemetry via ``read_telemetry`` and the run-dir usage artifact
        via ``load_usage_sidecar``, then writes the combined result back to the
        sidecar.
        """
        ...


class ISkillsMemoryProtocol(ABC):
    """Memory-v2 signal scan: read topics and observations, emit a report."""

    @abstractmethod
    def scan_memory(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
    ) -> MemoryReport:
        """Read ``$GROK_HOME/memory-v2`` topics and observations.

        A hardcoded monthly (30-day) window is used; no day window override
        or watermark is exposed. Never edits memory files.
        """
        ...


__all__ = [
    "ISkillsMemoryProtocol",
    "ISkillsPhraseProtocol",
    "ISkillsTracesProtocol",
    "ISkillsUsageProtocol",
]

_layer_symbols = {
    "ISkillsMemoryProtocol": ISkillsMemoryProtocol,
    "ISkillsPhraseProtocol": ISkillsPhraseProtocol,
    "ISkillsTracesProtocol": ISkillsTracesProtocol,
    "ISkillsUsageProtocol": ISkillsUsageProtocol,
    "GROK_HOME_ENV": GROK_HOME_ENV,
    "MIN_SESSIONS_DEFAULT": MIN_SESSIONS_DEFAULT,
    "MIN_TURNS_DEFAULT": MIN_TURNS_DEFAULT,
    "GrokHomeMissingError": GrokHomeMissingError,
    "NoSessionsError": NoSessionsError,
    "ObservabilityError": ObservabilityError,
}
