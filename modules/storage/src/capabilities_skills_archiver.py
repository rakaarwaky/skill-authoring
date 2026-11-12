"""Skills archiver capability (AES capabilities layer).

Implements ``ISkillsArchiverProtocol``: plan/apply an archive of a skill
into ``_archive/`` (dry-run by default). Delegates the physical move and
sidecar state update to ``SkillsRestore``.

Shared helpers (``resolve_skill_dir``, ``assert_within_root``,
``archive_root``) live in ``utility_skills_mutation`` (shared kernel)
so the archiver never imports a sibling capability.

Every computed destination is asserted to remain inside the skills root
at plan time **and** re-checked at apply time, so a symlink created
between the two fails closed instead of writing outside the pack.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.common.taxonomy_common_error import (
    MutationConflictError,
    SkillsUsageError,
)
from shared.src.common.taxonomy_common_vo import (
    MutationOutcome,
    MutationPlan,
    SkillName,
    SkillsRoot,
)
from shared.src.common.utility_common_skills import assert_within_root, resolve_skill_dir
from shared.src.maintenance.utility_lifecycle_support import archive_skill
from shared.src.maintenance.utility_skills_mutation import archive_root
from shared.src.storage.contract_storage_protocol import (
    ISkillsArchiverProtocol,
)

__all__ = ["SkillsArchiver"]

# ─── Block 1: Module Declaration ──────────────
class SkillsArchiver(ISkillsArchiverProtocol):
    """Plans and applies an archive of a skill into ``_archive/``.

    Archive state and path containment come from the shared kernel, so
    the archiver never imports a sibling capability.
    """

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ─────────────
    def plan_archive(self, skill: SkillName, root: SkillsRoot) -> MutationPlan:
        """Resolve an archive; the skill lands at ``_archive/<cat>/<skill>/``."""
        skills_root = Path(root)
        source = resolve_skill_dir(skill, skills_root)
        category = source.parent.name
        destination = archive_root(skills_root) / category / source.name

        if destination.exists():
            raise MutationConflictError(
                f"Archive destination already exists: {destination}"
            )

        assert_within_root(destination, skills_root)

        return MutationPlan(
            kind="archive",
            source=source,
            destination=destination,
            root=skills_root,
        )

    def apply_archive(self, plan: MutationPlan) -> MutationOutcome:
        """Execute an archive plan; re-checks containment first."""
        root = plan.root
        if plan.source is None or plan.destination is None:
            raise SkillsUsageError("Archive plan is missing its paths")

        # Fail-closed containment guard before we hand off to lifecycle.
        assert_within_root(plan.destination, root)

        skill_name = plan.source.name
        archive_skill(skill_name, root)
        return MutationOutcome(message="archived")

    # ─── Block 3: Module Helpers ─────────
    def __repr__(self) -> str:
        return "SkillsArchiver()"
