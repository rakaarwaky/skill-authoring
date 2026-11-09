"""Observability-domain capability contracts (AES contract layer, ABC traits).

One seam for the trace scan: scan sessions and mine repeated phrases.
Capabilities implement this; the composition root injects it into the
agent. No import of sibling domain contracts — observability keeps
its own seams.

No implementation code here — ABCs only, bodies are ``...``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.observability.taxonomy_observability_entity import ScanResult
from shared.src.observability.taxonomy_observability_response import ObservabilityResult
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
        """Walk ``$GROK_HOME/sessions`` and return a compact scan outcome.

        Writes ``manifest.json`` plus ``sessions/*.json`` into *run_dir*.
        """

    @abstractmethod
    def build_phrases(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        min_sessions: int = 2,
    ) -> PhrasesReport:
        """Mine repeated exact prompts and repeated instruction lines from session records."""


class ISkillsObservabilityAggregate(ABC):
    """Single entry point over observability-side ops."""

    @abstractmethod
    def execute(self, grok_home: GrokHome, run_dir: TraceRunDir) -> ObservabilityResult:
        """Run the observability scan; return the result."""
        ...


__all__ = [
    "ISkillsObservabilityAggregate",
    "ISkillsTracesProtocol",
]

_layer_symbols = {
    "ISkillsObservabilityAggregate": ISkillsObservabilityAggregate,
    "ISkillsTracesProtocol": ISkillsTracesProtocol,
}
