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
#: The run directory one trace scan writes into (``report.md``, ``.session/``).
TraceRunDir = NewType("TraceRunDir", str)
#: A turn is one user utterance in a trace session. ``Turns`` carries the
#: ordered tuple of turn strings instead of a bare primitive ``tuple``.
Turns = NewType("Turns", tuple[str, ...])


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


@dataclass(frozen=True)
class MemoryTopicRow:
    """One memory topic that matched a loaded skill or phrase stem."""

    workspace: str
    title: str
    path: str
    skill_names: tuple[str, ...] = ()
    quoted_lines: tuple[str, ...] = ()
    updated_at: str = ""
    matched_section: str | None = None


@dataclass(frozen=True)
class MemoryObservationRow:
    """One memory observation (_inbox) that carries a learn/stale/friction signal."""

    type: str
    quoted: str
    workspace: str = ""
    created_at: int = 0
    topic_hint: str = ""
    session_id: str = ""


@dataclass(frozen=True)
class MemoryReport:
    """Deterministic memory-v2 signals for one trace run."""

    topics: tuple[MemoryTopicRow, ...] = ()
    observations: tuple[MemoryObservationRow, ...] = ()
    keep_list: tuple[str, ...] = ()
    since_last: bool = False
    watermark: str = ""
    generated_at: str = ""


__all__ = [
    "GrokHome",
    "MemoryObservationRow",
    "MemoryReport",
    "MemoryTopicRow",
    "PhraseRow",
    "PhrasesReport",
    "TraceRunDir",
    "Turns",
]

_layer_symbols = {
    "GrokHome": GrokHome,
    "MemoryObservationRow": MemoryObservationRow,
    "MemoryReport": MemoryReport,
    "MemoryTopicRow": MemoryTopicRow,
    "PhraseRow": PhraseRow,
    "PhrasesReport": PhrasesReport,
    "TraceRunDir": TraceRunDir,
}
