"""Governance-domain utility functions — stateless, pure, domain-agnostic.

Module-level functions only — no classes, no state. Used by the locker,
piner, and mover capabilities across the governance feature.
"""

from __future__ import annotations

from pathlib import Path


def lock_state_filename(skills_root: Path) -> Path:
    """Return the path to the pack-level lock-state sidecar."""
    return skills_root / ".lock_state.json"


def default_lock_state(skill: str) -> str:
    """Return the default (unlocked) lock state for a skill."""
    return "active"


def is_locked(state: str) -> bool:
    """Return True when *state`` is the locked state."""
    return state == "locked"


def default_pin_state(skill: str) -> str:
    """Return the default (unpinned) pin state for a skill."""
    return "unpinned"


__all__ = [
    "default_lock_state",
    "default_pin_state",
    "is_locked",
    "lock_state_filename",
]

_layer_symbols = {
    "default_lock_state": default_lock_state,
    "default_pin_state": default_pin_state,
    "is_locked": is_locked,
    "lock_state_filename": lock_state_filename,
}
