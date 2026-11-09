"""Governance-domain errors (AES taxonomy layer).

Typed errors used by the locker, piner, and mover capabilities.
All errors extend ``SkillsError`` from the common layer and carry the
legacy message text plus an exit code.

No I/O, no imports from capabilities, agent, surface, root, or contract layers.
"""

from __future__ import annotations

from shared.src.common.taxonomy_common_error import SkillsError, SkillsUsageError
from shared.src.common.taxonomy_common_vo import ErrorMessage


class GovernanceError(SkillsError):
    """Base for governance-domain failures."""

    def __init__(self, message: ErrorMessage, *, exit_code: int = 2) -> None:
        super().__init__(message, exit_code=exit_code)


class SkillAlreadyLockedError(SkillsUsageError):
    """The skill is already locked."""


class SkillAlreadyPinnedError(SkillsUsageError):
    """The skill is already pinned."""


class SkillNotLockedError(SkillsUsageError):
    """The skill is not currently locked."""


class SkillNotPinnedError(SkillsUsageError):
    """The skill is not currently pinned."""


__all__ = [
    "GovernanceError",
    "SkillAlreadyLockedError",
    "SkillAlreadyPinnedError",
    "SkillNotLockedError",
    "SkillNotPinnedError",
]

_layer_symbols = {
    "GovernanceError": GovernanceError,
    "SkillAlreadyLockedError": SkillAlreadyLockedError,
    "SkillAlreadyPinnedError": SkillAlreadyPinnedError,
    "SkillNotLockedError": SkillNotLockedError,
    "SkillNotPinnedError": SkillNotPinnedError,
}
