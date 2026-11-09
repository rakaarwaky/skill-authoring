"""Observability-domain value objects (AES taxonomy layer).

Pure data for the phrase pipeline: phrase rows, reports, and type aliases
for grok home and run dir. No imports from utility, capabilities, agent,
root, or surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

#: The ``$GROK_HOME`` directory the phrase pipeline reads session traces from.
GrokHome = NewType("GrokHome", str)
#: The run directory one trace scan writes into (``report.md``, ``sessions/``).
TraceRunDir = NewType("TraceRunDir", str)


@dataclass(frozen=True)
class PhraseRow:
    """One repeated-phrase row: the normalized text, distinct-session count, occurrences."""

    phrase: str
    sessions: int
    occurrences: int
    session_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PhrasesReport:
    """Repeated exact prompts, repeated instruction lines, and prompt stems.

    Counts are distinct sessions. Surface projects this to a terminal listing
    (and optionally JSON).
    """

    exact_prompts: tuple[PhraseRow, ...] = ()
    stems: tuple[PhraseRow, ...] = ()
    repeated_instruction_lines: tuple[PhraseRow, ...] = ()


__all__ = [
    "GrokHome",
    "PhraseRow",
    "PhrasesReport",
    "TraceRunDir",
]

_layer_symbols = {
    "GrokHome": GrokHome,
    "PhraseRow": PhraseRow,
    "PhrasesReport": PhrasesReport,
    "TraceRunDir": TraceRunDir,
}
