"""Phrase scan capability (AES capabilities layer, self-contained in ``app``).

Scans ``$GROK_HOME/sessions`` and mines repeated prompts from ``<user_query>``
tags in session chat history. Depends only on the trace contract + taxonomy
from the shared kernel. Never imports ``skill-traces``.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from urllib.parse import unquote

from shared.src.observability.contract_observability_protocol import (
    ISkillsTracesProtocol,
)
from shared.src.observability.taxonomy_observability_entity import (
    ScanResult,
    TraceSessionRecord,
)
from shared.src.observability.taxonomy_observability_vo import (
    GrokHome,
    MemoryObservationRow,
    MemoryReport,
    MemoryTopicRow,
    PhraseRow,
    PhrasesReport,
    TraceRunDir,
)

__all__ = ["SkillsPhraseScan"]

# ─── Block 1: Module Declaration ──────────────
class SkillsPhraseScan(ISkillsTracesProtocol):
    """Scans sessions and mines repeated phrases."""

    _MIN_PHRASE_LEN = 12
    _MIN_LINE_WORDS = 5
    _MIN_LINE_CHARS = 24
    _EXACT_MIN_SESSIONS = 2
    _STEM_MIN_SESSIONS = 3
    _LINE_MIN_SESSIONS = 3
    _TOP = 60

    USER_QUERY_RE = re.compile(r"<user_query>(.*?)</user_query>", re.DOTALL)
    SLASH_RE = re.compile(r"/[a-z0-9-]+(\s+\S+){0,3}")
    SLASH_ONLY = re.compile(r"/[a-z0-9-]+(\s+\S+){0,3}$")
    DEFAULT_DROP_PATTERNS = (r"^the user invoked `/feedback`",)
    TURN_CAP = 2000
    _MEMORY_MAX_QUOTE = 200

    # Memory-v2 signal patterns (deterministic, no agent judgment).
    SKILL_PATH_RE = re.compile(r"[/\\]skills[/\\]([^/\\-][^/\\]*)[/\\]SKILL\.md$")
    SIGNAL_SECTION_RE = re.compile(r"(?m)^(##?\s+)(.*?)$")
    _KEEP_HINTS = ("never delete", "do not delete", "must keep", "keep-list", "keep list")
    _LEARN_HINTS = ("learn", "new skill", "create skill", "repeat", "habit")
    _STALE_HINTS = ("stale", "outdated", "wrong", "no longer")
    _UNLEARN_HINTS = ("unlearn", "retire", "remove", "delete")

    # ─── Block 2: Module Contract ─────────────
    def scan_sessions(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
    ) -> ScanResult:
        """Walk ``$GROK_HOME/sessions`` and return a compact scan outcome.

        A weekly (7-day) window is hardcoded — only sessions updated within
        the last 7 days are kept. ``since_last``, minimum-turn filter, and
        limit are removed; nothing is configurable by the caller.
        """
        grok_home = os.path.abspath(os.path.expanduser(grok_home))
        sessions_root = os.path.join(grok_home, "sessions")
        run_dir = os.path.abspath(run_dir)
        _clear_run_dir(run_dir)
        os.makedirs(os.path.join(run_dir, "sessions"), exist_ok=True)

        exclude_cwd = _default_exclude_cwd()
        drop_patterns = [re.compile(p, re.IGNORECASE) for p in self.DEFAULT_DROP_PATTERNS]

        # Hardcoded 7-day window: keep sessions newer than now - 7 days.
        cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=7)

        kept: list[dict] = []
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
                _normalize(r["turns"][0]) for r in kept if r["human_turns"] == 1
            )
            for r in kept:
                r["repeated_single_turn"] = bool(
                    r["human_turns"] == 1 and single[_normalize(r["turns"][0])] >= 3
                )
            kept = [r for r in kept if not r["repeated_single_turn"]]
            kept = [r for r in kept if not r["smoke_test"]]

            records: list[TraceSessionRecord] = []
            for i, r in enumerate(kept):
                r["index"] = i
                session_file = os.path.join(
                    run_dir, "sessions", f"{i:04d}-{r['id']}.json"
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
                days=7,
                since_last=False,
                min_turns=1,
                limit=0,
            )
            _write_usage(grok_home, run_dir, kept)

        return ScanResult(
            records=tuple(records),
            sessions_seen=seen,
            dropped=dict(dropped),
            min_turns=1,
            min_sessions=2,
        )

    def build_phrases(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
    ) -> PhrasesReport:
        """Read session records from ``run_dir`` and return repeated phrases.

        ``min_sessions`` is hardcoded to ``_EXACT_MIN_SESSIONS`` (2); nothing is
        configurable by the caller.
        """
        sessions_dir = os.path.join(run_dir, "sessions")
        exact: dict[str, list[str]] = defaultdict(list)
        stems: dict[str, list[str]] = defaultdict(list)
        lines: dict[str, set[str]] = defaultdict(set)

        min_sessions = self._EXACT_MIN_SESSIONS

        if os.path.isdir(sessions_dir):
            for name in sorted(os.listdir(sessions_dir)):
                if not name.endswith(".json"):
                    continue
                path = os.path.join(sessions_dir, name)
                try:
                    with open(path, encoding="utf-8") as f:
                        rec = json.load(f)
                except (OSError, ValueError):
                    continue
                rid = rec.get("id") or ""
                if rec.get("repeated_single_turn"):
                    continue
                for t in rec.get("turns") or []:
                    n = _normalize(t)
                    if len(n) < self._MIN_PHRASE_LEN:
                        continue
                    stripped = t.strip()
                    if self.SLASH_RE.fullmatch(stripped) or self.SLASH_ONLY.fullmatch(n):
                        continue
                    exact[n].append(rid)
                    words = n.split(" ")
                    if len(words) >= 6:
                        stems[" ".join(words[:12])].append(rid)
                    for ln in t.splitlines():
                        ln_n = _normalize(ln)
                        if (
                            len(ln_n.split(" ")) >= self._MIN_LINE_WORDS
                            and len(ln_n) >= self._MIN_LINE_CHARS
                        ):
                            lines[ln_n].add(rid)

        report = PhrasesReport(
            exact_prompts=self._top(exact, min_sessions, "phrase"),
            stems=self._top(stems, self._STEM_MIN_SESSIONS, "stem"),
            repeated_instruction_lines=self._top(lines, self._LINE_MIN_SESSIONS, "line"),
        )
        _write_phrases(run_dir, report)
        return report

    def scan_memory(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
    ) -> MemoryReport:
        """Read ``$GROK_HOME/memory-v2`` topics and observations.

        A weekly (7-day) window is hardcoded — only memory items modified
        within the last 7 days are kept. ``since_last`` and ``days`` are
        removed; nothing is configurable by the caller. Never edits memory
        files.
        """
        grok_home = os.path.abspath(os.path.expanduser(grok_home))
        memory_root = os.path.join(grok_home, "memory-v2")
        run_dir = os.path.abspath(run_dir)
        _clear_run_dir(run_dir)
        os.makedirs(run_dir, exist_ok=True)

        # Hardcoded 7-day window: keep memory items mtime >= now - 7 days.
        cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=7)

        topics: list[MemoryTopicRow] = []
        observations: list[MemoryObservationRow] = []
        keep_skills: list[str] = []

        def keep_ok(path: str) -> bool:
            if cutoff is None:
                return True
            try:
                mtime = dt.datetime.fromtimestamp(os.path.getmtime(path), tz=dt.UTC)
            except OSError:
                return True
            return mtime >= cutoff

        topic_roots = []
        if os.path.isdir(os.path.join(memory_root, "global", "topics")):
            topic_roots.append(("global", os.path.join(memory_root, "global", "topics")))
        workspaces_root = os.path.join(memory_root, "workspaces")
        if os.path.isdir(workspaces_root):
            for ws in sorted(os.listdir(workspaces_root)):
                tdir = os.path.join(workspaces_root, ws, "topics")
                if os.path.isdir(tdir):
                    topic_roots.append((ws, tdir))

        for ws, tdir in topic_roots:
            for name in sorted(os.listdir(tdir)):
                if not name.endswith(".md"):
                    continue
                path = os.path.join(tdir, name)
                if not keep_ok(path):
                    continue
                try:
                    with open(path, encoding="utf-8", errors="replace") as f:
                        text = f.read()
                except OSError:
                    continue

                # H1 title
                title = ""
                title_m = re.match(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
                if title_m:
                    title = title_m.group(1).strip()

                skill_names: list[str] = []
                quoted: list[str] = []
                matched_section: str | None = None
                low = text.lower()
                for hint in self._LEARN_HINTS:
                    if hint in low:
                        matched_section = "learn"
                        break
                for hint in self._STALE_HINTS:
                    if hint in low:
                        matched_section = "stale"
                        break
                for hint in self._UNLEARN_HINTS:
                    if hint in low:
                        matched_section = "unlearn"
                        break
                for hint in self._KEEP_HINTS:
                    if hint in low:
                        matched_section = "keep"
                        break

                # Skill names: lines that name a skill-like token.
                for m in self.SKILL_PATH_RE.finditer(text):
                    candidate = m.group(1)
                    if candidate not in skill_names:
                        skill_names.append(candidate)

                # Short quotes of lines that mention a skill or a known hint.
                for line in text.splitlines():
                    ln = line.strip()
                    if not ln or len(ln) > self._MEMORY_MAX_QUOTE:
                        continue
                    ln_low = ln.lower()
                    if any(s in ln_low for s in skill_names) or any(
                        h in ln_low for h in (
                            *self._KEEP_HINTS, *self._LEARN_HINTS,
                            *self._STALE_HINTS, *self._UNLEARN_HINTS,
                        )
                    ):
                        q = ln[: self._MEMORY_MAX_QUOTE]
                        if q not in quoted:
                            quoted.append(q)
                        if len(quoted) >= 6:
                            break

                topics.append(
                    MemoryTopicRow(
                        workspace=ws,
                        title=title,
                        path=path,
                        skill_names=tuple(skill_names),
                        quoted_lines=tuple(quoted),
                        updated_at=dt.datetime.fromtimestamp(
                            os.path.getmtime(path), tz=dt.UTC
                        ).isoformat(timespec="seconds"),
                        matched_section=matched_section,
                    )
                )

        if os.path.isdir(workspaces_root):
            for ws in sorted(os.listdir(workspaces_root)):
                inbox = os.path.join(workspaces_root, ws, "observations", "_inbox")
                if not os.path.isdir(inbox):
                    continue
                for name in sorted(os.listdir(inbox)):
                    if not name.endswith(".md"):
                        continue
                    path = os.path.join(inbox, name)
                    if not keep_ok(path):
                        continue
                    try:
                        with open(path, encoding="utf-8", errors="replace") as f:
                            text = f.read()
                    except OSError:
                        continue
                    front, body = _split_frontmatter(text)
                    ob_type = str(front.get("type", "") or "")
                    if ob_type not in ("friction", "stale", "learn"):
                        continue
                    quote = body.strip()[: self._MEMORY_MAX_QUOTE]
                    observations.append(
                        MemoryObservationRow(
                            type=ob_type,
                            quoted=quote,
                            workspace=ws,
                            created_at=int(front.get("created_at") or 0) or 0,
                            topic_hint=str(front.get("topic_hint") or ""),
                            session_id=str(front.get("session_id") or ""),
                        )
                    )

        for t in topics:
            if t.matched_section == "keep":
                for s in t.skill_names:
                    if s not in keep_skills:
                        keep_skills.append(s)

        keep_skills.sort()

        report = MemoryReport(
            topics=tuple(topics),
            observations=tuple(observations),
            keep_list=tuple(keep_skills),
            since_last=False,
            watermark=cutoff.isoformat(),
            generated_at=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        )

        # Persist memory.json into the run dir (deterministic material).
        with open(os.path.join(run_dir, "memory.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "source": "memory-v2",
                    "generated_at": report.generated_at,
                    "since_last": report.since_last,
                    "watermark": report.watermark,
                    "topics": [
                        {
                            "workspace": t.workspace,
                            "title": t.title,
                            "path": t.path,
                            "skill_names": list(t.skill_names),
                            "quoted_lines": list(t.quoted_lines),
                            "updated_at": t.updated_at,
                            "matched_section": t.matched_section,
                        }
                        for t in report.topics
                    ],
                    "observations": [
                        {
                            "type": o.type,
                            "quoted": o.quoted,
                            "workspace": o.workspace,
                            "created_at": o.created_at,
                            "topic_hint": o.topic_hint,
                            "session_id": o.session_id,
                        }
                        for o in report.observations
                    ],
                    "keep_list": list(report.keep_list),
                },
                f,
                indent=1,
                ensure_ascii=False,
            )

        return report

    # ─── Block 3: Module Helpers ─────────
    @staticmethod
    def _top(data: dict, min_count: int, key_name: str) -> tuple[PhraseRow, ...]:
        rows: list[PhraseRow] = []
        for k, ids in data.items():
            id_list = list(ids)
            sessions = len(set(id_list))
            if sessions >= min_count:
                rows.append(
                    PhraseRow(
                        phrase=k[:400],
                        sessions=sessions,
                        occurrences=len(id_list),
                        session_ids=tuple(sorted(set(id_list))[:8]),
                    )
                )
        rows.sort(key=lambda x: (-x.sessions, -x.occurrences, x.phrase))
        return tuple(rows[: SkillsPhraseScan._TOP])


def _read_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Split a memory file into (frontmatter dict, body text). Returns ({}, text) when none."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    header = text[4:end]
    body = text[end + 5 :]
    front: dict = {}
    for raw in header.splitlines():
        if ":" not in raw:
            continue
        key, _, val = raw.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            front[key] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
        elif val.startswith('"') and val.endswith('"'):
            front[key] = val[1:-1]
        else:
            front[key] = val
    return front, body


def _parse_time(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def _under(path: str, base: str) -> bool:
    path, base = os.path.normcase(os.path.normpath(path)), os.path.normcase(
        os.path.normpath(base)
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


def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


def _scan_session(sess_dir: str, summary: dict, drop_patterns: list[re.Pattern]) -> dict | None:
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
                    for m in SkillsPhraseScan.SLASH_RE.findall(q):
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
            t[: SkillsPhraseScan.TURN_CAP]
            + ("…" if len(t) > SkillsPhraseScan.TURN_CAP else "")
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
    found = [m.strip() for m in SkillsPhraseScan.USER_QUERY_RE.findall(txt)]
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


def _clear_run_dir(run_dir: str) -> None:
    """Remove all existing files under *run_dir* before a fresh write.

    The ``learn`` folder itself is kept; only its contents (manifest.json,
    usage.json, phrase.json, memory.json, sessions/) are wiped. This runs at
    the start of ``scan_sessions`` and ``scan_memory`` so a new invocation
    never leaves stale session records from a prior run behind.
    """
    run_dir = os.path.abspath(run_dir)
    if not os.path.isdir(run_dir):
        return
    for entry in os.listdir(run_dir):
        path = os.path.join(run_dir, entry)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def _write_usage(
    grok_home: str,
    run_dir: str,
    kept: list[dict],
) -> None:
    catalog_path = os.path.expanduser("~/.agents/skills/catalog.json")
    # Pinned skills (sac pin) live in the centralized .usage.json sidecar.
    # Fold the flag into usage.json so downstream curation (skill-traces)
    # can exclude pinned skills from unused/delete actions.
    sidecar_path = os.path.expanduser("~/.agents/skills/.usage.json")
    pinned: set[str] = set()
    if os.path.isfile(sidecar_path):
        try:
            with open(sidecar_path, encoding="utf-8") as f:
                for sname, rec in json.load(f).items():
                    if isinstance(rec, dict) and rec.get("pinned"):
                        pinned.add(sname)
        except (OSError, ValueError):
            pass
    skills_map: dict[str, dict] = {}
    if os.path.isfile(catalog_path):
        try:
            with open(catalog_path, encoding="utf-8") as f:
                cat = json.load(f)
            for s in cat.get("skills", []):
                name = s.get("name")
                cat_name = s.get("category", "")
                p = os.path.expanduser(f"~/.agents/skills/{cat_name}/{name}/SKILL.md")
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

    usage: dict[str, dict] = defaultdict(
        lambda: {
            "used_count": 0,
            "sessions": [],
            "last_used": None,
            "via": Counter(),
        }
    )
    unknown_slash: Counter[str] = Counter()

    for r in kept:
        sid = r.get("id") or ""
        updated = r.get("updated_at") or ""
        for name, n in (r.get("skills_loaded") or {}).items():
            u = usage[name]
            u["used_count"] += n
            if sid and sid not in u["sessions"] and len(u["sessions"]) < 8:
                u["sessions"].append(sid)
            if updated > (u["last_used"] or ""):
                u["last_used"] = updated
            u["via"]["skill_file_read"] += n
        for name, n in (r.get("slash_commands") or {}).items():
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
    for name, item in sorted(skills_map.items()):
        u = usage.get(name)
        rec = dict(item)
        rec["pinned"] = name in pinned
        rec["used_count"] = u["used_count"] if u else 0
        rec["sessions"] = u["sessions"] if u else []
        rec["last_used"] = u["last_used"] if u else None
        rec["via"] = dict(u["via"]) if u else {}
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
        "kept_sessions": len(kept),
        "items": items,
        "unused_loaded": unused,
        "slash_commands_with_no_loaded_skill": dict(unknown_slash.most_common()),
        "mcp_servers_used_but_not_in_local_config": {},
        "note": "hooks and managed-gateway MCP servers are not visible in local config; count is None when it cannot be measured",
    }
    with open(os.path.join(run_dir, "usage.json"), "w", encoding="utf-8") as f:
        json.dump(usage_data, f, indent=1, ensure_ascii=False)


def _write_phrases(run_dir: str, report: PhrasesReport) -> None:
    data = {
        "exact_prompts": [
            {
                "phrase": r.phrase,
                "sessions": r.sessions,
                "occurrences": r.occurrences,
                "session_ids": list(r.session_ids),
            }
            for r in report.exact_prompts
        ],
        "prompt_stems_12_words": [
            {
                "phrase": r.phrase,
                "sessions": r.sessions,
                "occurrences": r.occurrences,
                "session_ids": list(r.session_ids),
            }
            for r in report.stems
        ],
        "repeated_instruction_lines": [
            {
                "phrase": r.phrase,
                "sessions": r.sessions,
                "occurrences": r.occurrences,
                "session_ids": list(r.session_ids),
            }
            for r in report.repeated_instruction_lines
        ],
        "note": "counts are distinct sessions; single-turn sessions repeated 3+ times are excluded as likely automation",
    }
    with open(os.path.join(run_dir, "phrases.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)

