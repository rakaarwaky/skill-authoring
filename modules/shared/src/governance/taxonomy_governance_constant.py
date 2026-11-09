"""Governance-domain constants (AES taxonomy layer).

Constants consumed by the locker, piner, and mover capabilities:
state names, exit codes, and lock/pin field keys.

Pure literals only — no functions, no I/O.
"""

from __future__ import annotations

from typing import Final

#: Lock states a skill can hold.
LOCK_STATE_ACTIVE: Final = "active"
LOCK_STATE_LOCKED: Final = "locked"

#: Pin states a skill can hold.
PIN_STATE_UNPINNED: Final = "unpinned"
PIN_STATE_PINNED: Final = "pinned"

#: The sidecar file holding lock/pin state per skill.
LOCK_STATE_FILENAME: Final = ".lock_state.json"

__all__ = [
    "LOCK_STATE_ACTIVE",
    "LOCK_STATE_FILENAME",
    "LOCK_STATE_LOCKED",
    "PIN_STATE_PINNED",
    "PIN_STATE_UNPINNED",
]

_layer_symbols = {
    "LOCK_STATE_ACTIVE": LOCK_STATE_ACTIVE,
    "LOCK_STATE_LOCKED": LOCK_STATE_LOCKED,
    "LOCK_STATE_FILENAME": LOCK_STATE_FILENAME,
    "PIN_STATE_PINNED": PIN_STATE_PINNED,
    "PIN_STATE_UNPINNED": PIN_STATE_UNPINNED,
}
