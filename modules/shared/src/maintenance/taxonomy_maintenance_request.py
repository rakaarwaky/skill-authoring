"""Maintenance-domain request value objects (AES taxonomy layer).

The typed envelope for the maintenance aggregate: ``MaintenanceRequest``
carries the verb and optional skill name, plus optional flags.
``MaintenanceVerb`` names every operation the maintenance aggregate understands.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import NewType

from shared.src.common.taxonomy_common_vo import SkillName

SkillsRoot = NewType("SkillsRoot", Path)
"""An explicit skills root; ``None`` on a request means 'use the default'."""


class MaintenanceVerb(Enum):
    """Consumer verbs carried by the maintenance aggregate's single entry point."""

    PRUNE = "prune"
    PURGE = "purge"
    ARCHIVE = "archive"
    RESTORE = "restore"


@dataclass(frozen=True)
class MaintenanceRequest:
    """The aggregate entry point's single argument (AES401)."""

    verb: MaintenanceVerb
    skill: SkillName | None = None
    root: SkillsRoot | None = None
    flags: Mapping[str, str] = field(default_factory=dict)


__all__ = [
    "MaintenanceRequest",
    "MaintenanceVerb",
    "SkillsRoot",
]

_layer_symbols = {
    "MaintenanceRequest": MaintenanceRequest,
    "MaintenanceVerb": MaintenanceVerb,
    "SkillsRoot": SkillsRoot,
}
