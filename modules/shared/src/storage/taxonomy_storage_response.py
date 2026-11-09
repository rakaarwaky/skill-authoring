"""Storage-domain response value objects (AES taxonomy layer).

The typed response envelope: ``StorageResponse`` is what the surface
renders after one storage aggregate op. Payload fields are populated per
verb and never re-read from a capability.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shared.src.common.taxonomy_common_vo import SkillRecord


@dataclass(frozen=True)
class StorageResponse:
    """Response to a storage aggregate request.

    ``ok``/``verb``/``exit_code``/``message`` form the command contract.
    Payload fields are populated per verb: ``records`` for LIST,
    ``manifest`` for BOOTSTRAP, ``content`` for READ.
    """

    ok: bool
    verb: str
    exit_code: int = 0
    message: str = ""
    records: tuple[SkillRecord, ...] = ()
    manifest: dict[str, object] | None = None
    content: str | None = None
    root: Path | None = None


__all__ = ["StorageResponse"]

_layer_symbols = {
    "StorageResponse": StorageResponse,
}
