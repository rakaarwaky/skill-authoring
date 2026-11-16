"""Governance-domain constants (AES taxonomy layer).

Constants consumed by the piner and mover capabilities:
state names, exit codes, and pin field keys.

Pure literals only — no functions, no I/O.
"""

from __future__ import annotations

from typing import Final

#: Pin states a skill can hold.
PIN_STATE_UNPINNED: Final = "unpinned"
PIN_STATE_PINNED: Final = "pinned"

__all__ = [
    "PIN_STATE_PINNED",
    "PIN_STATE_UNPINNED",
]

_layer_symbols = {
    "PIN_STATE_PINNED": PIN_STATE_PINNED,
    "PIN_STATE_UNPINNED": PIN_STATE_UNPINNED,
}
