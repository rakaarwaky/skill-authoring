"""Skill prune capability (AES capabilities layer).

One command, two passes:
  1. archive idle skills (idle >= days, default 30) — active → archived
  2. purge archived skills (archived >= purge_days, default 60) — delete

Safety rails:
  - pinned skills are never archived
  - cron-referenced skills are never archived
  - purge never touches a skill still active in the pack
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from shared.src.common.taxonomy_common_vo import SkillName
from shared.src.common.utility_common_skills import (
    default_pack_root,
    iter_skill_mds,
)
from shared.src.design.taxonomy_design_vo import (
    load_lifecycle_config,
)
from shared.src.maintenance.contract_maintenance_protocol import (
    ISkillsPrunerProtocol,
)
from shared.src.maintenance.taxonomy_maintenance_request import SkillsRoot
from shared.src.maintenance.taxonomy_maintenance_response import (
    MaintenanceResponse,
)
from shared.src.maintenance.utility_lifecycle_support import (
    ACTIVE,
    _cron_referenced,
    _parse_iso,
    archive_skill,
    delete_record,
    read_record,
)
from shared.src.maintenance.utility_maintenance_core import (
    default_prune_ttl_days,
    default_purge_ttl_days,
)
from shared.src.maintenance.utility_skills_mutation import archive_root

__all__ = ["SkillsPrune"]


# ─── Block 1: Module Declaration ──────────────
class SkillsPrune(ISkillsPrunerProtocol):
    """Prune capability: archive-idle pass + purge-old-archive pass."""

# ─── Block 2: Module Contract ─────────────
    def prune(
        self,
        root: SkillsRoot | None = None,
        days: int | None = None,
        purge_days: int | None = None,
        dry_run: bool = False,
    ) -> MaintenanceResponse:
        pack_root = Path(root) if root is not None else default_pack_root()
        config = load_lifecycle_config(pack_root)

        # Pass 1: archive idle skills
        archive_after = (
            days
            if days is not None
            else getattr(config, "archive_after_days", None) or default_prune_ttl_days()
        )
        if archive_after < 1:
            raise ValueError(f"prune days must be >= 1, got {archive_after}")

        archive_cutoff = datetime.now(UTC) - timedelta(days=archive_after)
        archived: list[dict] = []
        kept: list[dict] = []

        for skill_md in iter_skill_mds(pack_root):
            skill_dir = skill_md.parent
            name = skill_dir.name
            record = read_record(skill_dir, pack_root)
            state = record.get("state", ACTIVE)

            if record.get("pinned"):
                kept.append({"skill": name, "state": state, "reason": "pinned"})
                continue

            if _cron_referenced(pack_root, name):
                kept.append({"skill": name, "state": state, "reason": "cron-referenced"})
                continue

            ts_str = (
                record.get("last_activity_at")
                or record.get("created_at")
            )
            is_idle = False
            if ts_str:
                dt = _parse_iso(ts_str)
                if dt is not None and dt <= archive_cutoff:
                    is_idle = True
            else:
                is_idle = True

            if is_idle:
                if not dry_run:
                    archive_skill(name, pack_root)
                archived.append({"skill": name, "days_idle": archive_after})
            else:
                kept.append({"skill": name, "state": state})

        # Pass 2: purge old archives
        purge_after = (
            purge_days
            if purge_days is not None
            else getattr(config, "archive_ttl_days", 0) or default_purge_ttl_days()
        )
        purged: list[dict] = []

        if purge_after > 0:
            purge_cutoff = datetime.now(UTC) - timedelta(days=purge_after)
            arch_root = archive_root(pack_root)
            if arch_root.is_dir():
                for skill_md in iter_skill_mds(arch_root):
                    skill_dir = skill_md.parent
                    name = skill_dir.name
                    record = read_record(skill_dir, pack_root)
                    archived_at = record.get("archived_at")
                    mtime = datetime.fromtimestamp(skill_dir.stat().st_mtime, tz=UTC)
                    dt = _parse_iso(archived_at) if archived_at else mtime
                    cmp_dt = max(dt, mtime) if dt else mtime
                    if cmp_dt <= purge_cutoff:
                        if not dry_run:
                            shutil.rmtree(skill_dir)
                            delete_record(skill_dir, pack_root)
                        purged.append({"skill": name, "archived_at": str(archived_at)})

        message = f"archived={len(archived)} purged={len(purged)} kept={len(kept)}"
        return MaintenanceResponse(
            ok=True,
            verb="prune",
            records=tuple(SkillName(r["skill"]) for r in archived + purged),
            message=message,
            dry_run=dry_run,
        )


# ─── Block 3: Module Helpers ─────────