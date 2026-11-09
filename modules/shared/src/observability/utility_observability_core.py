"""Observability-domain utility functions — stateless, pure, domain-agnostic.

Module-level functions only — no classes, no state. Used by the trace
scan and phrase-mining capabilities across the observability feature.
"""

from __future__ import annotations

from pathlib import Path


def default_run_dir(skills_root: Path) -> Path:
    """Return the default trace run directory under the skills root."""
    return skills_root / ".trace_runs"


def validate_min_turns(min_turns: int) -> int:
    """Clamp *min_turns* to at least 1."""
    return max(1, min_turns)


def validate_min_sessions(min_sessions: int) -> int:
    """Clamp *min_sessions* to at least 1."""
    return max(1, min_sessions)


__all__ = [
    "default_run_dir",
    "validate_min_sessions",
    "validate_min_turns",
]

_layer_symbols = {
    "default_run_dir": default_run_dir,
    "validate_min_sessions": validate_min_sessions,
    "validate_min_turns": validate_min_turns,
}
