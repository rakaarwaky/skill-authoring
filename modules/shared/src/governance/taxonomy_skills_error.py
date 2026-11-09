"""Skills-domain errors (AES governance layer).

The governance layer's error surface re-exports the canonical error
hierarchy from the common layer. All six error classes are consumed
across every module domain (discovery, design, storage, maintenance,
governance, observability). Capabilities import these from here or
from ``shared.src.common.taxonomy_common_error`` directly.
"""

from __future__ import annotations

from shared.src.common.taxonomy_common_error import (
    CategoryNameError,
    MutationConflictError,
    SkillNotFoundError,
    SkillsError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.common.taxonomy_common_vo import ErrorMessage

__all__ = [
    "CategoryNameError",
    "ErrorMessage",
    "GovernanceError",
    "MutationConflictError",
    "SkillNotFoundError",
    "SkillsError",
    "SkillsRootError",
    "SkillsUsageError",
]


class GovernanceError(SkillsError):
    """Base error for the governance domain's typed error hierarchy."""

    def __init__(self, message: ErrorMessage, *, exit_code: int = 2) -> None:
        super().__init__(message, exit_code=exit_code)


_layer_symbols = {
    "CategoryNameError": CategoryNameError,
    "ErrorMessage": ErrorMessage,
    "GovernanceError": GovernanceError,
    "MutationConflictError": MutationConflictError,
    "SkillNotFoundError": SkillNotFoundError,
    "SkillsError": SkillsError,
    "SkillsRootError": SkillsRootError,
    "SkillsUsageError": SkillsUsageError,
}
