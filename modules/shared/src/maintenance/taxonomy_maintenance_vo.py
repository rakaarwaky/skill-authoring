"""Maintenance-domain value objects (AES taxonomy layer).

Pure data for prune/purge decisions and maintenance result envelopes.
No imports from utility, capabilities, agent, root, or surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

#: Opaque identifier for a maintenance operation (prune / purge / archive / restore).
MaintenanceOpId = NewType("MaintenanceOpId", str)


@dataclass(frozen=True)
class MaintenanceOp:
    """One maintenance operation record: op id, verb, skill, and outcome."""

    op_id: MaintenanceOpId
    verb: str
    skill: str
    applied: bool = False


__all__ = ["MaintenanceOp", "MaintenanceOpId"]

_layer_symbols = {
    "MaintenanceOp": MaintenanceOp,
    "MaintenanceOpId": MaintenanceOpId,
}
