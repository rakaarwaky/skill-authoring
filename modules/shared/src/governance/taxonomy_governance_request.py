"""Governance-domain request value objects (AES taxonomy layer).

The typed envelope for the governance aggregate: ``GovernanceRequest``
carries the verb and skill name, plus optional flags. ``GovernanceVerb``
names every operation the governance aggregate understands.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import NewType

from shared.src.common.taxonomy_common_vo import SkillsRoot

SkillQuery = NewType("SkillQuery", str)
"""A skill name / identifier to look up in the pack."""


class GovernanceVerb(Enum):
    """Consumer verbs carried by the governance aggregate's single entry point."""

    LOCK = "lock"
    UNLOCK = "unlock"
    PIN = "pin"
    UNPIN = "unpin"
    MOVE = "move"


@dataclass(frozen=True)
class GovernanceRequest:
    """The aggregate entry point's single argument (AES401)."""

    verb: GovernanceVerb
    query: SkillQuery = field(default_factory=lambda: SkillQuery(""))
    root: SkillsRoot | None = None
    flags: Mapping[str, str] = field(default_factory=dict)


__all__ = [
    "GovernanceRequest",
    "GovernanceVerb",
    "SkillQuery",
    "SkillsRoot",
]

_layer_symbols = {
    "GovernanceRequest": GovernanceRequest,
    "GovernanceVerb": GovernanceVerb,
    "SkillQuery": SkillQuery,
    "SkillsRoot": SkillsRoot,
}
