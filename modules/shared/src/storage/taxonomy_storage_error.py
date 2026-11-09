"""Storage-domain errors (AES taxonomy layer).

Typed errors used by the pack bootstrap and skill-pack reader capabilities.
All errors extend ``SkillsError`` from the common layer.

No I/O, no imports from capabilities, agent, surface, root, or contract layers.
"""

from __future__ import annotations

from shared.src.common.taxonomy_common_error import SkillsError, SkillsUsageError
from shared.src.common.taxonomy_common_vo import ErrorMessage


class StorageError(SkillsError):
    """Base for storage-domain failures."""

    def __init__(self, message: ErrorMessage, *, exit_code: int = 2) -> None:
        super().__init__(message, exit_code=exit_code)


class PackRootMissingError(SkillsUsageError):
    """The skills pack root is missing or not a directory."""


class SkillPackNotFoundError(SkillsUsageError):
    """No ``SKILL.md`` found for the referenced skill."""


__all__ = ["PackRootMissingError", "SkillPackNotFoundError", "StorageError"]

_layer_symbols = {
    "PackRootMissingError": PackRootMissingError,
    "SkillPackNotFoundError": SkillPackNotFoundError,
    "StorageError": StorageError,
}
