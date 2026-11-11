"""Skill piner capability (AES capabilities layer).

Toggles the pinned flag on a skill's sidecar record.
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
    ISkillsPinerProtocol,
)
from shared.src.governance.taxonomy_governance_constant import (
    PIN_STATE_PINNED,
    PIN_STATE_UNPINNED,
)
from shared.src.governance.taxonomy_governance_entity import PinState

__all__ = ["SkillsPiner"]


# ─── Block 1: Module Declaration ──────────────
class SkillsPiner(ISkillsPinerProtocol):
    """Piner capability: pin/unpin verbs."""

# ─── Block 2: Module Contract ─────────────
    def pin(self, skill: str, root: SkillsRoot | None = None) -> PinState:
        pack_root = Path(root) if root is not None else default_pack_root()
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            raise ValueError(f"No skill directory found for: {skill}")
        set_field(skill_dir, "pinned", True)
        return PinState(skill=skill, pinned=True)

    def unpin(self, skill: str, root: SkillsRoot | None = None) -> PinState:
        pack_root = Path(root) if root is not None else default_pack_root()
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            raise ValueError(f"No skill directory found for: {skill}")
        set_field(skill_dir, "pinned", False)
        return PinState(skill=skill, pinned=False)
# ─── Block 3: Module Helpers ─────────
