"""Governance-domain response value objects (AES taxonomy layer).

The typed response envelope: ``GovernanceResponse`` is what the surface
renders after one governance aggregate op. Payload fields are populated
per verb and never re-read from a capability.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from shared.src.governance.taxonomy_governance_entity import LockState, PinState

if TYPE_CHECKING:
    from shared.src.design.taxonomy_design_vo import MutationOutcome, MutationPlan


@dataclass(frozen=True)
class GovernanceResponse:
    """Response to a governance aggregate request.

    ``ok``/``verb``/``exit_code``/``message`` form the command contract.
    Payload fields are populated per verb: ``lock_state`` for LOCK/UNLOCK,
    ``pin_state`` for PIN/UNPIN, ``plan`` and ``outcome`` for MOVE.
    """

    ok: bool
    verb: str
    exit_code: int = 0
    message: str = ""
    lock_state: LockState | None = None
    pin_state: PinState | None = None
    plan: MutationPlan | None = None
    outcome: MutationOutcome | None = None
    root: Path | None = None


__all__ = ["GovernanceResponse"]

_layer_symbols = {
    "GovernanceResponse": GovernanceResponse,
}
