"""Maintenance-domain response value objects (AES taxonomy layer).

The typed response envelope: ``MaintenanceResponse`` is what the surface
renders after one maintenance aggregate op. Payload fields are populated
per verb and never re-read from a capability.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shared.src.common.taxonomy_common_vo import SkillName


@dataclass(frozen=True)
class MaintenanceResponse:
    """Response to a maintenance aggregate request.

    ``ok``/``verb``/``exit_code``/``message`` form the command contract.
    Payload fields are populated per verb: ``records`` for PRUNE/PURGE,
    ``applied`` for ARCHIVE/RESTORE.
    """

    ok: bool
    verb: str
    exit_code: int = 0
    message: str = ""
    records: tuple[SkillName, ...] = ()
    applied: bool = False
    root: Path | None = None


__all__ = ["MaintenanceResponse"]

_layer_symbols = {
    "MaintenanceResponse": MaintenanceResponse,
}
