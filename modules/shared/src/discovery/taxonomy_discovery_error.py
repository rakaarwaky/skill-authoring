"""Discovery-domain errors (AES taxonomy layer).

Typed errors used by the discovery feature: missing skill root, bad query,
and catalog drift. All errors extend ``SkillsError`` from the common layer
and carry the legacy message text plus an exit code.

No I/O, no imports from capabilities, agent, surface, root, or contract layers.
"""

from __future__ import annotations

from shared.src.common.taxonomy_common_error import SkillsError, SkillsUsageError
from shared.src.common.taxonomy_common_vo import ErrorMessage


class DiscoveryError(SkillsError):
    """Base for discovery-domain failures."""

    def __init__(self, message: ErrorMessage, *, exit_code: int = 2) -> None:
        super().__init__(message, exit_code=exit_code)


class QueryEmptyError(SkillsUsageError):
    """The caller supplied an empty discovery query."""


class CatalogMissingError(SkillsUsageError):
    """The tracked catalog.json is missing or unreadable."""


__all__ = ["CatalogMissingError", "DiscoveryError", "QueryEmptyError"]

_layer_symbols = {
    "CatalogMissingError": CatalogMissingError,
    "DiscoveryError": DiscoveryError,
    "QueryEmptyError": QueryEmptyError,
}
