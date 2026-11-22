"""Observability-domain entities (AES taxonomy layer).

Identity-bearing domain records for trace sessions and phrase rows.
Pure data: no I/O, no imports from utility, capabilities, agent, root,
or surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from shared.src.observability.taxonomy_observability_constant import (
    MIN_SESSIONS_DEFAULT,
    MIN_TURNS_DEFAULT,
)
from shared.src.observability.taxonomy_observability_vo import Turns


@dataclass(frozen=True)
class TraceSessionRecord:
    """One compact per-session record from a trace scan."""

    id: str
    index: int
    cwd: str
    updated_at: str = ""
    turns: Turns = ()
    slash_commands: Mapping[str, int] = field(default_factory=dict)
    skills_loaded: Mapping[str, int] = field(default_factory=dict)
    trace_path: str = ""


@dataclass(frozen=True)
class ScanResult:
    """Outcome of one tracker scan: kept records plus scan counters."""

    records: tuple[TraceSessionRecord, ...]
    sessions_seen: int
    dropped: Mapping[str, int] = field(default_factory=dict)
    min_turns: int = MIN_TURNS_DEFAULT
    min_sessions: int = MIN_SESSIONS_DEFAULT


__all__ = ["ScanResult", "TraceSessionRecord"]

_layer_symbols = {
    "ScanResult": ScanResult,
    "TraceSessionRecord": TraceSessionRecord,
}
