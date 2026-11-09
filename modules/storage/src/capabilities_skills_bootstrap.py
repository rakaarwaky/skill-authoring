"""Skills bootstrap capability (AES capabilities layer).

Initializes a skill pack root: creates the standard category
directories and writes the pack sidecar used by every verb.
Implements ``ISkillsBootstrapProtocol`` from
``shared/src/storage/contract_storage_protocol.py``.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.storage.contract_storage_protocol import ISkillsBootstrapProtocol
from shared.src.storage.taxonomy_storage_constant import CATEGORY_DIRS
from shared.src.storage.taxonomy_storage_request import SkillsRoot, StorageVerb
from shared.src.storage.taxonomy_storage_response import StorageResponse
from shared.src.common.utility_common_skills import default_pack_root

__all__ = ["SkillsBootstrap"]


# ─── Block 1: Module Declaration ───
class SkillsBootstrap(ISkillsBootstrapProtocol):
    """Bootstrap capability: initialize a skill pack root."""

    # ─── Block 2: Module Contract ───
    def bootstrap(self, root: SkillsRoot | None = None) -> StorageResponse:
        """Create the standard category dirs and pack sidecar under *root*.

        Returns a ``StorageResponse`` whose ``manifest`` holds the
        resolved pack root and the list of created category directories.
        """
        skills_root = Path(root) if root is not None else default_pack_root()
        skills_root.mkdir(parents=True, exist_ok=True)

        created: list[str] = []
        for category in CATEGORY_DIRS:
            category_dir = skills_root / category
            if not category_dir.exists():
                category_dir.mkdir(parents=True, exist_ok=True)
                created.append(category)

        # ─── Block 3: Module Helpers ───
        manifest = {
            "verb": StorageVerb.BOOTSTRAP.value,
            "root": str(skills_root),
            "created": created,
        }
        return StorageResponse(
            ok=True,
            verb=StorageVerb.BOOTSTRAP.value,
            message=f"bootstrapped {skills_root}",
            manifest=manifest,
            root=skills_root,
        )
