"""Skill locker capability (AES capabilities layer).

Toggles the locked flag on a skill's sidecar record.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.common.taxonomy_common_vo import SkillsRoot
from shared.src.common.utility_common_skills import (
    default_pack_root,
    find_skill_dir,
    set_field,
)
from shared.src.governance.contract_governance_protocol import (
    ISkillsLockerProtocol,
)
from shared.src.governance.taxonomy_governance_constant import (
    LOCK_STATE_ACTIVE,
    LOCK_STATE_LOCKED,
)
from shared.src.governance.taxonomy_governance_entity import LockState

__all__ = ["SkillsLocker"]


# ─── Block 1: Module Declaration ──────────────
class SkillsLocker(ISkillsLockerProtocol):
    """Locker capability: lock/unlock verbs."""

# ─── Block 2: Module Contract ─────────────
    def lock(self, skill: str, root: SkillsRoot | None = None) -> LockState:
        pack_root = Path(root) if root is not None else default_pack_root()
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            raise ValueError(f"No skill directory found for: {skill}")
        set_field(skill_dir, "locked", True)
        return LockState(skill=skill, state=LOCK_STATE_LOCKED)

    def unlock(self, skill: str, root: SkillsRoot | None = None) -> LockState:
        pack_root = Path(root) if root is not None else default_pack_root()
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            raise ValueError(f"No skill directory found for: {skill}")
        set_field(skill_dir, "locked", False)
        return LockState(skill=skill, state=LOCK_STATE_ACTIVE)
# ─── Block 3: Module Helpers ─────────
