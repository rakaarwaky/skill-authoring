"""Observability-domain errors (AES taxonomy layer).

Typed errors used by the trace scan and phrase-mining capabilities.
All errors extend ``SkillsError`` from the common layer.

No I/O, no imports from capabilities, agent, surface, root, or contract layers.
"""

from __future__ import annotations

from shared.src.common.taxonomy_common_error import (
    SkillsError,
    SkillsUsageError,
)
from shared.src.common.taxonomy_common_vo import ErrorMessage


class ObservabilityError(SkillsError):
    """Base for observability-domain failures."""

    def __init__(self, message: ErrorMessage, *, exit_code: int = 2) -> None:
        super().__init__(message, exit_code=exit_code)


class GrokHomeMissingError(SkillsUsageError):
    """The ``$GROK_HOME`` directory does not exist."""


class NoSessionsError(SkillsUsageError):
    """No session traces found to scan."""


__all__ = ["GrokHomeMissingError", "NoSessionsError", "ObservabilityError"]

_layer_symbols = {
    "GrokHomeMissingError": GrokHomeMissingError,
    "NoSessionsError": NoSessionsError,
    "ObservabilityError": ObservabilityError,
}
