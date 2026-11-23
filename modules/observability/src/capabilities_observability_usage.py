"""Usage-scan trace capability (AES capabilities layer).

Produces ``usage.json`` run-dir artifact from session records. Reads the kept
session records returned by ``scan_sessions`` and computes per-skill usage
analytics (used_count, sessions, last_used, via).
Depends only on the trace contract + taxonomy from the shared kernel plus the
shared run-dir clearing utility. Never imports other capabilities (AES201).
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict

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

__all__ = ["SkillsObservabilityUsage"]


# ─── Block 1: Module Declaration ──────────────
class SkillsObservabilityUsage(ISkillsUsageProtocol):
    """Computes usage analytics from session records; writes usage.json.

    Implements exactly one protocol (ISkillsUsageProtocol) with one public
    method (write_usage). No stubs, no NotImplementedError, no cross-capability
    imports (AES304 clean; AES403 single-contract; AES201 allowed cell). It does
    NOT fold into the ``.usage.json`` sidecar — that is telemetry's job,
    orchestrated by the agent.
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
        telemetry; sidecar fold delegated to telemetry in PR 4.

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
