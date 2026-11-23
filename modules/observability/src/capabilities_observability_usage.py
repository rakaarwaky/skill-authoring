"""Usage-scan trace capability (AES capabilities layer).

Produces the ``usage.json`` run-dir artifact from session records and owns
the ``.usage.json`` sidecar lifecycle (seed, reanchor, curated report,
``record_use``, ``fold_used_count_into_sidecar``). Reads the kept session
records returned by ``scan_sessions`` and computes per-skill usage analytics
(used_count, sessions, last_used, via).
Depends only on the trace contract + taxonomy from the shared kernel plus the
shared run-dir clearing and lifecycle utilities. Never imports other
capabilities (AES201).
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
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
    ISkillsUsageProtocol,
)
from shared.src.observability.taxonomy_observability_entity import (
    TraceSessionRecord,
)
from shared.src.observability.taxonomy_observability_vo import (
    GrokHome,
    TraceRunDir,
)
from shared.src.observability.utility_observability_run_dir import clear_run_dir
from shared.src.observability.utility_observability_usage import (
    load_usage_sidecar,
    read_telemetry,
)

__all__ = ["SkillsObservabilityUsage"]


# ─── Block 1: Module Declaration ──────────────
class SkillsObservabilityUsage(ISkillsUsageProtocol):
    """Computes usage analytics from session records; writes usage.json.

    Implements ISkillsUsageProtocol: write_usage plus the absorbed telemetry
    surface (seed_record_if_missing, reanchor_clock, curated_report, record_use,
    fold_used_count_into_sidecar). No stubs, no NotImplementedError, no
    cross-capability imports (AES304 clean; AES403 single-contract; AES201
    allowed cell).
    """

    # ─── Block 2: Module Contract ─────────────
    def write_usage(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        records: tuple[TraceSessionRecord, ...],
    ) -> list[dict]:
        """Compute per-skill usage analytics; write ``usage.json``; return items.

        Consumes the frozen ``TraceSessionRecord`` dataclasses returned by
        ``scan_sessions`` (via ``ScanResult.records``) using attribute access
        (``r.id``, ``r.updated_at``, ``r.skills_loaded``, ``r.slash_commands``).
        No ``.get()`` / dict access is used — ``TraceSessionRecord`` is a frozen
        dataclass with no mapping interface. Returns per-skill records
        (used_count, sessions, last_used, via, pinned) for the agent to hand to
        telemetry; sidecar fold is implemented on this class via
        ``fold_used_count_into_sidecar``.

        Clearing ownership: clears ONLY ``usage.json`` via
        ``clear_run_dir(run_dir, action="usage")``. It never clears ``sessions/``
        or ``manifest.json`` — those are owned by ``scan_sessions`` (which already
        ran). Re-wiping ``sessions/`` here would delete the records this capability
        is about to read.
        """
        # Clears usage.json only; never sessions/ or manifest.json.
        clear_run_dir(run_dir, action="usage")
        catalog_path = os.path.expanduser("~/.agents/skills/catalog.json")
        # Pinned skills (sac pin) live in the centralized .usage.json sidecar.
        # Read the sidecar once so we can fold the ``pinned`` flag into
        # usage.json (downstream curation excludes pinned skills from
        # unused/delete actions).
        sidecar_path = os.path.expanduser("~/.agents/skills/.usage.json")
        sidecar_data: dict[str, dict] = {}
        if os.path.isfile(sidecar_path):
            try:
                with open(sidecar_path, encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    sidecar_data = {
                        k: v for k, v in loaded.items() if isinstance(v, dict)
                    }
            except (OSError, ValueError):
                sidecar_data = {}
        pinned: set[str] = {
            sname for sname, rec in sidecar_data.items() if rec.get("pinned")
        }
        skills_map: dict[str, dict] = {}
        if os.path.isfile(catalog_path):
            try:
                with open(catalog_path, encoding="utf-8") as f:
                    cat = json.load(f)
                for s in cat.get("skills", []):
                    name = s.get("name")
                    cat_name = s.get("category", "")
                    p = os.path.expanduser(
                        f"~/.agents/skills/{cat_name}/{name}/SKILL.md"
                    )
                    if os.path.isfile(p):
                        skills_map[name] = {
                            "kind": "skill",
                            "name": name,
                            "source": "repo-pack",
                            "path": p,
                            "protected": "git-tracked",
                            "referenced_by": [],
                            "plugin": None,
                            "plugin_state": None,
                            "loaded": True,
                            "disabled_by_name": False,
                            "in_slash_mru": False,
                        }
            except (OSError, ValueError):
                pass
        bundled_dir = os.path.join(grok_home, "bundled", "skills")
        if os.path.isdir(bundled_dir):
            for name in sorted(os.listdir(bundled_dir)):
                p = os.path.join(bundled_dir, name, "SKILL.md")
                if os.path.isfile(p) and name not in skills_map:
                    skills_map[name] = {
                        "kind": "skill",
                        "name": name,
                        "source": "bundled",
                        "path": p,
                        "protected": "bundled",
                        "referenced_by": [],
                        "plugin": None,
                        "plugin_state": None,
                        "loaded": True,
                        "disabled_by_name": False,
                        "in_slash_mru": False,
                    }
        skill_bodies: dict[str, str] = {}
        for name, item in skills_map.items():
            try:
                with open(item["path"], encoding="utf-8", errors="replace") as f:
                    skill_bodies[name] = f.read()
            except OSError:
                pass
        for name, item in skills_map.items():
            pat = re.compile(
                r"(`/?"
                + re.escape(name)
                + r"`|(?<![\w-])/"
                + re.escape(name)
                + r"(?![\w-])|skills/"
                + re.escape(name)
                + r"(?![\w-]))"
            )
            refs = [
                other
                for other, body in skill_bodies.items()
                if other != name and pat.search(body)
            ]
            item["referenced_by"] = sorted(set(refs))

        def _new_usage_record() -> dict:
            return {
                "used_count": 0,
                "sessions": [],
                "last_used": None,
                "via": Counter(),
            }

        usage: dict[str, dict] = defaultdict(_new_usage_record)
        unknown_slash: Counter[str] = Counter()
        for r in records:
            sid = r.id or ""
            updated = r.updated_at or ""
            for name, n in (r.skills_loaded or {}).items():
                u = usage[name]
                u["used_count"] += n
                if sid and sid not in u["sessions"] and len(u["sessions"]) < 8:
                    u["sessions"].append(sid)
                if updated > (u["last_used"] or ""):
                    u["last_used"] = updated
                u["via"]["skill_file_read"] += n
            for name, n in (r.slash_commands or {}).items():
                if name in skills_map:
                    u = usage[name]
                    u["used_count"] += n
                    if sid and sid not in u["sessions"] and len(u["sessions"]) < 8:
                        u["sessions"].append(sid)
                    if updated > (u["last_used"] or ""):
                        u["last_used"] = updated
                    u["via"]["slash"] += n
                else:
                    unknown_slash[name] += n
        items = []

        # ─── Block 3: Module Helpers ─────────
        for name, item in sorted(skills_map.items()):
            entry: dict | None = usage.get(name)
            rec = dict(item)
            rec["pinned"] = name in pinned
            if entry is not None:
                rec["used_count"] = entry["used_count"]
                rec["sessions"] = entry["sessions"]
                rec["last_used"] = entry["last_used"]
                rec["via"] = dict(entry["via"])
            else:
                rec["used_count"] = 0
                rec["sessions"] = []
                rec["last_used"] = None
                rec["via"] = {}
            items.append(rec)
        unused = [
            i["name"]
            for i in items
            if i["kind"] == "skill"
            and i["loaded"]
            and i["used_count"] == 0
            and not i["in_slash_mru"]
            and not i.get("pinned")
        ]
        usage_data = {
            "kept_sessions": len(records),
            "items": items,
            "unused_loaded": unused,
            "slash_commands_with_no_loaded_skill": dict(unknown_slash.most_common()),
            "mcp_servers_used_but_not_in_local_config": {},
            "note": "hooks and managed-gateway MCP servers are not visible in local config; count is None when it cannot be measured",
        }
        with open(os.path.join(run_dir, "usage.json"), "w", encoding="utf-8") as f:
            json.dump(usage_data, f, indent=1, ensure_ascii=False)
        return items

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
        sidecar_path = pack_usage_path()
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
