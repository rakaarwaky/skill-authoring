"""Usage-scan trace capability (AES capabilities layer).

Produces the ``usage.json`` run-dir artifact from session records and owns
the pack ``usage.json`` lifecycle (seed, reanchor, curated report,
``record_use``, ``fold_used_count_into_usage``). Also owns ``scan_sessions``
(self-contained session scan: 30-day window, ``.session/`` records,
``manifest.json`` write, run-dir clearing) — no separate scan capability.
Depends only on the trace contract + taxonomy from the shared kernel plus the
shared run-dir clearing and lifecycle utilities. Never imports other
capabilities (AES201).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

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
    ScanResult,
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

    Also owns scan_sessions: walks ``$GROK_HOME/sessions`` within a hardcoded
    30-day window, writes ``.session/`` records and ``manifest.json`` to the
    run dir, and returns a ScanResult. The scan no longer goes through a
    separate capability class.
    """

    USER_QUERY_RE = re.compile(r"<user_query>(.*?)</user_query>", re.DOTALL)
    SLASH_RE = re.compile(r"/[a-z0-9-]+(\s+\S+){0,3}")
    DEFAULT_DROP_PATTERNS = (r"^the user invoked `/feedback`",)
    TURN_CAP = 2000

    # ─── Block 2: Module Contract ─────────────
    def scan_sessions(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
    ) -> ScanResult:
        """Walk ``$GROK_HOME/sessions`` and return a compact scan outcome.

        A hardcoded 30-day window keeps sessions updated within the last 30
        days. Writes ``.session/`` records and ``manifest.json`` to run_dir,
        clearing those plus ``usage.json`` first. Returns per-session
        ``TraceSessionRecord`` tuples plus scan counters.
        """
        grok_home = os.path.abspath(os.path.expanduser(grok_home))
        sessions_root = os.path.join(grok_home, "sessions")
        run_dir = os.path.abspath(run_dir)
        _clear_run_dir(run_dir, action="usage")
        os.makedirs(os.path.join(run_dir, ".session"), exist_ok=True)
        exclude_cwd = _default_exclude_cwd()
        drop_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.DEFAULT_DROP_PATTERNS
        ]
        # Hardcoded 30-day window: keep sessions newer than now - 30 days.
        cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=30)
        kept: list[dict] = []
        records: list[TraceSessionRecord] = []
        seen = 0
        dropped: Counter[str] = Counter()
        if os.path.isdir(sessions_root):
            for enc_cwd in sorted(os.listdir(sessions_root)):
                cwd_dir = os.path.join(sessions_root, enc_cwd)
                if not os.path.isdir(cwd_dir):
                    continue
                for sid in sorted(os.listdir(cwd_dir)):
                    sess_dir = os.path.join(cwd_dir, sid)
                    if not os.path.isdir(sess_dir):
                        continue
                    seen += 1
                    summ_path = os.path.join(sess_dir, "summary.json")
                    if not os.path.isfile(summ_path):
                        dropped["no_summary"] += 1
                        continue
                    try:
                        summary = _read_json(summ_path)
                    except (OSError, ValueError):
                        dropped["summary_unreadable"] += 1
                        continue
                    if not isinstance(summary, dict):
                        dropped["summary_unreadable"] += 1
                        continue
                    info = summary.get("info") or {}
                    cwd = info.get("cwd") or unquote(enc_cwd)
                    if any(_under(cwd, p) for p in exclude_cwd) or any(
                        s in cwd for s in ("grok-e2e",)
                    ):
                        dropped["excluded_cwd"] += 1
                        continue
                    if cutoff is not None:
                        ts = _parse_time(summary.get("updated_at"))
                        if ts is None or ts < cutoff:
                            dropped["older_than_window"] += 1
                            continue
                    rec = _scan_session(sess_dir, summary, drop_patterns)
                    if rec is None or rec["human_turns"] < 1:
                        dropped["no_human_turns"] += 1
                        continue
                    kept.append(rec)
            kept.sort(key=lambda r: r.get("updated_at") or "", reverse=True)
            single = Counter(
                _normalize_str(r["turns"][0]) for r in kept if r["human_turns"] == 1
            )
            for r in kept:
                r["repeated_single_turn"] = bool(
                    r["human_turns"] == 1
                    and single[_normalize_str(r["turns"][0])] >= 3
                )
            kept = [r for r in kept if not r["repeated_single_turn"]]
            kept = [r for r in kept if not r["smoke_test"]]
            for i, r in enumerate(kept):
                r["index"] = i
                session_file = os.path.join(
                    run_dir, ".session", f"{i:04d}-{r['id']}.json"
                )
                with open(session_file, "w", encoding="utf-8") as f:
                    json.dump(r, f, indent=1, ensure_ascii=False)
                records.append(_record_from_dict(r))
        _write_manifest(
            grok_home,
            run_dir,
            records,
            kept,
            seen,
            dropped,
            days=30,
            since_last=False,
            min_turns=1,
            limit=0,
        )
        return ScanResult(
            records=tuple(records),
            sessions_seen=seen,
            dropped=dict(dropped),
            min_turns=1,
            min_sessions=2,
        )

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

    # ─── Block 4: scan_sessions module-level helpers ─────────


def _read_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _parse_time(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def _under(path: str, base: str) -> bool:
    path, base = (
        os.path.normcase(os.path.normpath(path)),
        os.path.normcase(os.path.normpath(base)),
    )
    return path == base or path.startswith(base.rstrip(os.sep) + os.sep)


def _default_exclude_cwd() -> list[str]:
    tmp = os.environ.get("TMPDIR", os.path.expanduser("~/.cache"))
    return sorted(
        {
            os.path.normcase(os.path.normpath(p))
            for p in (
                tmp,
                os.path.realpath(tmp),
                os.path.expanduser("~/.cache"),
                os.path.expanduser("~/.local/share"),
            )
        }
    )


def _normalize_str(s: str) -> str:
    return " ".join(s.strip().lower().split())


def _scan_session(
    sess_dir: str, summary: dict, drop_patterns: list[re.Pattern]
) -> dict | None:
    """Scan one session dir; return a compact record dict or None."""
    chat = os.path.join(sess_dir, "chat_history.jsonl")
    if not os.path.isfile(chat):
        return None
    turns: list[str] = []
    tools: Counter[str] = Counter()
    skill_loads: Counter[str] = Counter()
    skill_load_paths: dict[str, str] = {}
    slash: Counter[str] = Counter()
    paths_touched: Counter[str] = Counter()
    subagents = 0
    workflow_launches = 0
    parse_errors = 0
    dropped_turns = 0
    skill_path_re = re.compile(r"[/\\]skills[/\\]([^/\\]+)[/\\]SKILL\.md$")
    with open(chat, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                parse_errors += 1
                continue
            if not isinstance(r, dict):
                parse_errors += 1
                continue
            t = r.get("type")
            if t == "user" and not r.get("synthetic_reason"):
                for q in _human_turns(r.get("content")):
                    if any(p.search(q) for p in drop_patterns):
                        dropped_turns += 1
                        continue
                    turns.append(q)
                    for m in SkillsObservabilityUsage.SLASH_RE.findall(q):
                        slash[m] += 1
            elif t == "assistant":
                for call in r.get("tool_calls") or []:
                    if not isinstance(call, dict):
                        continue
                    name = call.get("name") or ""
                    tools[name] += 1
                    try:
                        a = json.loads(call.get("arguments") or "{}")
                    except ValueError:
                        a = {}
                    if not isinstance(a, dict):
                        a = {}
                    elif name == "spawn_subagent":
                        subagents += 1
                    elif name == "workflow":
                        workflow_launches += 1
                    target = a.get("target_file") or a.get("file_path") or a.get("path")
                    if isinstance(target, str) and target:
                        sm = skill_path_re.search(target)
                        if sm:
                            skill_loads[sm.group(1)] += 1
                            skill_load_paths.setdefault(sm.group(1), target)
                        elif name in ("read_file", "write", "search_replace"):
                            paths_touched[target] += 1
    if not turns:
        return None
    real_tools = sum(n for name, n in tools.items() if name != "send_feedback")
    smoke_test = real_tools == 0 and all(len(t.split()) < 3 for t in turns)
    info = summary.get("info") or {}
    cwd = info.get("cwd") or ""
    git_root = summary.get("git_root_dir") or ""
    base = git_root or cwd
    dirs: Counter[str] = Counter()
    for p, n in paths_touched.items():
        rel = p
        if base and _under(p, base):
            rel = os.path.relpath(p, base)
        parts = [x for x in re.split(r"[\\/]+", rel) if x]
        key = "/".join(parts[:2]) if len(parts) > 2 else (parts[0] if parts else rel)
        dirs[key] += n
    capped_turns = [
        (
            t[: SkillsObservabilityUsage.TURN_CAP]
            + ("…" if len(t) > SkillsObservabilityUsage.TURN_CAP else "")
        )
        for t in turns
    ]
    return {
        "id": summary.get("id") or os.path.basename(sess_dir),
        "cwd": cwd,
        "git_root": git_root,
        "branch": summary.get("head_branch") or "",
        "title": summary.get("generated_title") or "",
        "updated_at": summary.get("updated_at") or "",
        "model": summary.get("current_model_id"),
        "human_turns": len(turns),
        "dropped_turns": dropped_turns,
        "parse_errors": parse_errors,
        "smoke_test": smoke_test,
        "turns": capped_turns,
        "slash_commands": dict(slash.most_common()),
        "skills_loaded": dict(skill_loads.most_common()),
        "skill_load_paths": skill_load_paths,
        "tools": dict(tools.most_common(25)),
        "subagent_spawns": subagents,
        "workflow_launches": workflow_launches,
        "top_dirs_touched": dict(dirs.most_common(10)),
        "trace_path": chat,
        "repeated_single_turn": False,
    }


def _human_turns(content) -> list[str]:
    if isinstance(content, str):
        txt = content
    elif isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text") or "")
            elif isinstance(c, str):
                parts.append(c)
        txt = "\n".join(parts)
    else:
        txt = ""
    found = [m.strip() for m in SkillsObservabilityUsage.USER_QUERY_RE.findall(txt)]
    return [t for t in found if t]


def _record_from_dict(r: dict) -> TraceSessionRecord:
    return TraceSessionRecord(
        id=r["id"],
        index=r.get("index", 0),
        cwd=r.get("cwd", ""),
        updated_at=r.get("updated_at") or "",
        turns=tuple(r.get("turns") or ()),
        slash_commands=r.get("slash_commands") or {},
        skills_loaded=r.get("skills_loaded") or {},
        trace_path=r.get("trace_path") or "",
    )


def _write_manifest(
    grok_home: str,
    run_dir: str,
    records: list[TraceSessionRecord],
    kept: list[dict],
    seen: int,
    dropped: Counter[str],
    days: int,
    since_last: bool,
    min_turns: int,
    limit: int,
) -> None:
    manifest = {
        "grok_home": grok_home,
        "run_dir": run_dir,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "sessions_seen": seen,
        "sessions_kept": len(kept),
        "dropped": dict(dropped),
        "human_turns_total": sum(r["human_turns"] for r in kept),
        "kept": [
            {
                "index": r["index"],
                "id": r["id"],
                "cwd": r["cwd"],
                "turns": r["human_turns"],
                "updated_at": r["updated_at"],
                "title": r.get("title", ""),
            }
            for r in kept
        ],
        "params": {
            "days": days,
            "since_last": since_last,
            "min_turns": min_turns,
            "limit": limit,
        },
    }
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)


def _clear_run_dir(run_dir: str, action: str = "usage") -> None:
    """Remove existing files under *run_dir* before a fresh write.

    The run dir itself is kept; only the artifacts relevant to *action* are
    wiped so a new invocation never leaves stale records from a prior run
    behind. ``usage`` clears .session/, manifest.json, usage.json. The
    scan_sessions method uses this with action="usage" to clear its own
    artifacts before writing new session records and the manifest.
    """
    run_dir = os.path.abspath(run_dir)
    if not os.path.isdir(run_dir):
        return
    targets = {
        "phrases": (".session", "manifest.json", "phrases.json"),
        "usage": (".session", "manifest.json", "usage.json"),
        "memory": ("memory.json",),
    }.get(action, ())
    for entry in os.listdir(run_dir):
        if entry not in targets:
            continue
        path = os.path.join(run_dir, entry)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
