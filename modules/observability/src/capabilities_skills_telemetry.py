"""Skill telemetry capability (AES capabilities layer).

Reads and bumps the per-skill ``.usage.json`` sidecar: seeding the record,
reanchoring the clock, counting uses, and emitting the curated
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
from shared.src.observability.taxonomy_observability_entity import (
    TraceSessionRecord,
)
from shared.src.observability.taxonomy_observability_vo import (
    GrokHome,
    TraceRunDir,
)
from shared.src.observability.utility_observability_usage import (
    load_usage_sidecar,
    read_telemetry,
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
                    used_count=int(rec.get("used_count", 0)),
                    activity_window_start=rec.get("activity_window_start"),
                )
            )
        rows.sort(key=lambda r: r.name)
        return tuple(rows)

    def record_use(self, skill: str, root: SkillsRoot) -> None:
        self._bump(skill, root, "used_count")

    def fold_used_count_into_sidecar(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        records: tuple[TraceSessionRecord, ...],
    ) -> None:
        """Fold per-skill ``used_count`` analytics into ``.usage.json`` sidecar.

        Reads telemetry via ``read_telemetry`` and the run-dir usage artifact
        via ``load_usage_sidecar``, then writes the combined result back to the
        sidecar.
        """
        sidecar_path = Path(grok_home).expanduser() / ".usage.json" if grok_home else pack_usage_path()
        sidecar_data = read_telemetry(sidecar_path)
        usage_data = load_usage_sidecar(run_dir)
        items = usage_data.get("items", []) if isinstance(usage_data, dict) else []

        now = _now_iso()
        legacy_count_fields = ("views", "uses", "use_count", "view_count")
        changed = False
        for item in items:
            if item.get("kind") != "skill":
                continue
            name = item["name"]
            count = int(item.get("used_count", 0) or 0)
            existing = sidecar_data.get(name)
            if existing is None:
                record = _baseline_record()
            else:
                record = dict(existing)
            had_legacy = any(f in record for f in legacy_count_fields)
            if (
                record.get("used_count") == count
                and "used_count" in record
                and existing is not None
                and not had_legacy
                and record.get("sessions") == item.get("sessions", [])
                and record.get("last_used") == item.get("last_used")
                and record.get("via") == item.get("via", {})
            ):
                continue
            for f in legacy_count_fields:
                record.pop(f, None)
            record["used_count"] = count
            record["sessions"] = item.get("sessions", [])
            record["last_used"] = item.get("last_used")
            record["via"] = item.get("via", {})
            last_used = item.get("last_used")
            if last_used:
                record["last_activity_at"] = last_used
                record["activity_window_start"] = last_used
            else:
                record["last_activity_at"] = now
                record["activity_window_start"] = now
            sidecar_data[name] = record
            changed = True
        if not changed:
            return
        try:
            atomic_write_json(sidecar_path, sidecar_data)
        except OSError:
            pass

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
