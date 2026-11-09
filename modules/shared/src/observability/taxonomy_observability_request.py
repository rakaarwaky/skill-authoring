"""Observability-domain request value objects (AES taxonomy layer).

The typed envelope for the observability aggregate: ``ObservabilityRequest``
carries the op, the skill name or search query, and pack-root override.
``ObservabilityOp`` names every operation the observability aggregate understands.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import NewType

SkillQuery = NewType("SkillQuery", str)
"""A skill name / identifier to look up in the pack."""

SkillsRoot = NewType("SkillsRoot", Path)
"""An explicit skills root; ``None`` on a request means 'use the default'."""


class ObservabilityOp(StrEnum):
    """Operations the observability aggregate understands."""

    PHRASES = "phrases"
    SCAN = "scan"


@dataclass(frozen=True)
class ObservabilityRequest:
    """Input for one observability operation."""

    op: ObservabilityOp = ObservabilityOp.PHRASES
    query: SkillQuery = field(default_factory=lambda: SkillQuery(""))
    root: SkillsRoot | None = None
    apply: bool = False
    json: bool = False
    description: str = ""
    flags: Mapping[str, str] = field(default_factory=dict)


__all__ = [
    "ObservabilityOp",
    "ObservabilityRequest",
    "SkillQuery",
    "SkillsRoot",
]

_layer_symbols = {
    "ObservabilityOp": ObservabilityOp,
    "ObservabilityRequest": ObservabilityRequest,
    "SkillQuery": SkillQuery,
    "SkillsRoot": SkillsRoot,
}
