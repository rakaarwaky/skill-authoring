"""Skill telemetry capability (AES capabilities layer).

Reads and bumps the per-skill ``.usage.json`` sidecar: seeding the record,
reanchoring the clock, counting views, and emitting the curated
report consumed by the ``status`` / ``usage`` surface verbs.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.common.taxonomy_common_vo import SkillsRoot
from shared.src.common.utility_common_skills import iter_skill_mds
from shared.src.design.taxonomy_design_vo import TelemetryRow
from shared.src.maintenance.utility_lifecycle_support import (
    DEFAULT_STATE,
    _baseline_record,
    _normalize,
    _now_iso,
    _read_sidecar,
    _with_lock,
    pack_usage_path,
)
from shared.src.maintenance.utility_skills_mutation import atomic_write_json
from shared.src.observability.contract_observability_protocol import (
    ISkillsTelemetryProtocol,
)

__all__ = ["SkillsTelemetry"]


# ─── Block 1: Module Declaration ──────────────
class SkillsTelemetry(ISkillsTelemetryProtocol):
    """Telemetry capability: sidecar reads, bumps, and the curated report."""

    # ─── Block 2: Module Contract ─────────────
    def seed_record_if_missing(self, skill: str, root: SkillsRoot) -> None:
        skills_root = Path(root)
        path = pack_usage_path(skills_root)

        def work() -> None:
            data = _read_sidecar(path)
            if skill in data:
                return
            data[skill] = _baseline_record()
            try:
                atomic_write_json(path, data)
            except OSError:
                pass

        _with_lock(path, work)

    def reanchor_clock(self, skill: str, root: SkillsRoot) -> None:
        skills_root = Path(root)
        path = pack_usage_path(skills_root)

        def work() -> None:
            data = _read_sidecar(path)
            record = data.get(skill, {})
            record = _normalize(record) if record else _baseline_record()
            now = _now_iso()
            record["last_activity_at"] = now
            record["activity_window_start"] = now
            if not record.get("pinned", False):
                record["state"] = DEFAULT_STATE
            data[skill] = record
            try:
                atomic_write_json(path, data)
            except OSError:
                pass

        _with_lock(path, work)

    def curated_report(self, root: SkillsRoot) -> tuple[TelemetryRow, ...]:
        skills_root = Path(root)
        path = pack_usage_path(skills_root)
        data = _read_sidecar(path)
        rows: list[TelemetryRow] = []
        for skill_md in iter_skill_mds(skills_root):
            name = skill_md.parent.name
            rec = _normalize(data.get(name, {})) if name in data else _baseline_record()
            rows.append(
                TelemetryRow(
                    name=name,
                    state=str(rec.get("state", DEFAULT_STATE)),
                    pinned=bool(rec.get("pinned", False)),
                    created_by=rec.get("created_by"),
                    created_at=rec.get("created_at"),
                    first_seen_at=rec.get("first_seen_at"),
                    last_activity_at=rec.get("last_activity_at"),
                    archived_at=rec.get("archived_at"),
                    views=int(rec.get("views", 0)),
                    uses=int(rec.get("uses", 0)),
                    activity_window_start=rec.get("activity_window_start"),
                )
            )
        rows.sort(key=lambda r: r.name)
        return tuple(rows)

    def view(self, skill: str, root: SkillsRoot) -> None:
        self._bump(skill, root, "views")

    # ─── Block 3: Module Helpers ─────────
    def _bump(
        self,
        skill: str,
        root: SkillsRoot,
        counter_field: str,
        now_iso: str | None = None,
    ) -> None:
        skills_root = Path(root)
        path = pack_usage_path(skills_root)

        def work() -> None:
            data = _read_sidecar(path)
            record = data.get(skill, {})
            record = _normalize(record) if record else _baseline_record()
            current = record.get(counter_field, 0)
            record[counter_field] = (current if isinstance(current, int) else 0) + 1
            now = now_iso or _now_iso()
            record["last_activity_at"] = now
            record["activity_window_start"] = now
            if not record.get("pinned", False):
                record["state"] = DEFAULT_STATE
            data[skill] = record
            try:
                atomic_write_json(path, data)
            except OSError:
                pass

        _with_lock(path, work)
