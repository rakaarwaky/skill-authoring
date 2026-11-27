"""Usage-scan trace capability (AES capabilities layer).

Produces the ``usage.json`` run-dir artifact from session records and owns
the pack ``usage.json`` lifecycle (seed, reanchor, curated report,
``record_use``, ``fold_used_count_into_usage``). Reads the kept session
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
    FIELDS,
    _baseline_record,
    _find_item,
    _normalize,
    _now_iso,
    _read_usage,
    _write_usage,
    _with_lock,
    pack_usage_path,
)
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
)

__all__ = ["SkillsObservabilityUsage"]


# ─── Block 1: Module Declaration ──────────────
class SkillsObservabilityUsage(ISkillsUsageProtocol):
    """Computes usage analytics from session records; writes usage.json.

    Implements ISkillsUsageProtocol: write_usage plus the absorbed telemetry
    surface (seed_record_if_missing, reanchor_clock, curated_report, record_use,
    fold_used_count_into_usage). No stubs, no NotImplementedError, no
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
        telemetry; the pack-file fold is implemented on this class via
        ``fold_used_count_into_usage``.

        Clearing ownership: clears ONLY ``usage.json`` via
        ``clear_run_dir(run_dir, action="usage")``. It never clears ``.session/``
        or ``manifest.json`` — those are owned by ``scan_sessions`` (which already
        ran). Re-wiping ``.session/`` here would delete the records this capability
        is about to read.
        """
        # Clears usage.json only; never .session/ or manifest.json.
        clear_run_dir(run_dir, action="usage")
        catalog_path = os.path.expanduser("~/.agents/skills/catalog.json")
        # Pinned skills (sac pin) live in the pack usage.json.
        # Read its items once so we can fold the ``pinned`` flag and the
        # lifecycle fields into the new items (downstream curation excludes
        # pinned skills from unused/delete actions).
        central_path = os.path.expanduser("~/.agents/skills/usage.json")
        prev_items: dict[str, dict] = {}
        if os.path.isfile(central_path):
            try:
                with open(central_path, encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    for entry in loaded.get("items", []):
                        if isinstance(entry, dict) and "name" in entry:
                            prev_items[entry["name"]] = entry
            except (OSError, ValueError):
                pass
        pinned: set[str] = {
            sname for sname, rec in prev_items.items() if rec.get("pinned")
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
            # Seed lifecycle fields from the pack usage.json when present;
            # baseline the rest so every item is flat and complete.
            prev = prev_items.get(name)
            if prev is not None:
                for f in FIELDS:
                    if f in prev and f not in rec:
                        rec[f] = prev[f]
            for f in FIELDS:
                if f not in rec:
                    rec[f] = _baseline_record()[f]
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
        }
        with open(os.path.join(run_dir, "usage.json"), "w", encoding="utf-8") as f:
            json.dump(usage_data, f, indent=1, ensure_ascii=False)
        return items

    def seed_record_if_missing(self, skill: str, root: SkillsRoot) -> None:
        skills_root = Path(root)
        path = pack_usage_path(skills_root)

        def work() -> None:
            data = _read_usage(path)
            if _find_item(data, skill) is not None:
                return
            record = _baseline_record()
            record["name"] = skill
            data.setdefault("items", []).append(record)
            try:
                _write_usage(path, data)
            except OSError:
                pass

        _with_lock(path, work)

    def reanchor_clock(self, skill: str, root: SkillsRoot) -> None:
        skills_root = Path(root)
        path = pack_usage_path(skills_root)

        def work() -> None:
            data = _read_usage(path)
            record = _find_item(data, skill)
            if record is None:
                record = _baseline_record()
                record["name"] = skill
                data.setdefault("items", []).append(record)
            else:
                normalized = _normalize(record)
                for k, v in normalized.items():
                    record[k] = v
            now = _now_iso()
            record["last_activity_at"] = now
            record["activity_window_start"] = now
            if not record.get("pinned", False):
                record["state"] = DEFAULT_STATE
            try:
                _write_usage(path, data)
            except OSError:
                pass

        _with_lock(path, work)

    def curated_report(self, root: SkillsRoot) -> tuple[TelemetryRow, ...]:
        skills_root = Path(root)
        path = pack_usage_path(skills_root)
        data = _read_usage(path)
        rows: list[TelemetryRow] = []
        for skill_md in iter_skill_mds(skills_root):
            name = skill_md.parent.name
            rec = _normalize(_find_item(data, name)) if _find_item(data, name) else _baseline_record()
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

    def fold_used_count_into_usage(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        records: tuple[TraceSessionRecord, ...],
    ) -> None:
        """Fold per-skill ``used_count`` analytics into the pack ``usage.json``.

        Reads the run-dir ``usage.json`` artifact via ``load_usage_sidecar``
        and merges each item's analytics fields (used_count, sessions,
        last_used, via) into the corresponding entry in the central pack
        ``usage.json`` (flat ``items[]``), preserving lifecycle fields.
        """
        central_path = pack_usage_path()
        central = _read_usage(central_path)
        central_items: dict[str, dict] = {
            i["name"]: i for i in central.get("items", []) if "name" in i
        }
        usage_data = load_usage_sidecar(run_dir)
        items = usage_data.get("items", []) if isinstance(usage_data, dict) else []

        now = _now_iso()
        changed = False
        for item in items:
            if item.get("kind") != "skill":
                continue
            name = item["name"]
            count = int(item.get("used_count", 0) or 0)
            existing = central_items.get(name)
            if existing is None:
                record = _baseline_record()
                record["name"] = name
                central_items[name] = record
                central.setdefault("items", []).append(record)
            else:
                record = existing
            last_used = item.get("last_used")
            record["used_count"] = count
            record["sessions"] = item.get("sessions", [])
            record["last_used"] = last_used
            record["via"] = item.get("via", {})
            if last_used:
                record["last_activity_at"] = last_used
                record["activity_window_start"] = last_used
            else:
                record["last_activity_at"] = now
                record["activity_window_start"] = now
            changed = True
        if not changed:
            return
        try:
            _write_usage(central_path, central)
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
            data = _read_usage(path)
            record = _find_item(data, skill)
            if record is None:
                record = _baseline_record()
                record["name"] = skill
                data.setdefault("items", []).append(record)
            else:
                normalized = _normalize(record)
                for k, v in normalized.items():
                    record[k] = v
            current = record.get(counter_field, 0)
            record[counter_field] = (current if isinstance(current, int) else 0) + 1
            now = now_iso or _now_iso()
            record["last_activity_at"] = now
            record["activity_window_start"] = now
            if not record.get("pinned", False):
                record["state"] = DEFAULT_STATE
            try:
                _write_usage(path, data)
            except OSError:
                pass

        _with_lock(path, work)
