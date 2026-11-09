"""Storage-domain request value objects (AES taxonomy layer).

The typed envelope for the storage aggregate: ``StorageRequest`` carries
the verb, pack root, and optional skill name. ``StorageVerb`` names every
operation the storage aggregate understands.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import NewType

SkillsRoot = NewType("SkillsRoot", Path)
"""An explicit skills root; ``None`` on a request means 'use the default'."""


class StorageVerb(Enum):
    """Consumer verbs carried by the storage aggregate's single entry point."""

    BOOTSTRAP = "bootstrap"
    LIST = "list"
    READ = "read"


@dataclass(frozen=True)
class StorageRequest:
    """The aggregate entry point's single argument (AES401)."""

    verb: StorageVerb
    root: SkillsRoot | None = None
    query: str = ""
    flags: Mapping[str, str] = field(default_factory=dict)


__all__ = [
    "SkillsRoot",
    "StorageRequest",
    "StorageVerb",
]

_layer_symbols = {
    "StorageRequest": StorageRequest,
    "StorageVerb": StorageVerb,
    "SkillsRoot": SkillsRoot,
}
