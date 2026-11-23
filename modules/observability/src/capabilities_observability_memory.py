"""Memory-v2 signal scan capability (AES capabilities layer, self-contained in ``app``).

Reads ``$GROK_HOME/memory-v2`` topics and observations and writes
``memory.json`` into the run dir. Depends only on the trace contract,
taxonomy, and the shared run-dir utility from the shared kernel.
Never imports sibling capabilities.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re

from shared.src.observability.contract_observability_protocol import (
    ISkillsMemoryProtocol,
)
from shared.src.observability.taxonomy_observability_vo import (
    GrokHome,
    MemoryObservationRow,
    MemoryReport,
    MemoryTopicRow,
    TraceRunDir,
)
from shared.src.observability.utility_observability_run_dir import clear_run_dir

__all__ = ["SkillsObservabilityMemory"]

# ─── Block 1: Module Declaration ──────────────
class SkillsObservabilityMemory(ISkillsMemoryProtocol):
    """Reads memory-v2 topics and observations; emits a MemoryReport."""

    _MEMORY_MAX_QUOTE = 200
    # Memory-v2 signal patterns (deterministic, no agent judgment).
    SKILL_PATH_RE = re.compile(r"[/\\]skills[/\\]([^/\\-][^/\\]*)[/\\]SKILL\.md$")
    _KEEP_HINTS = (
        "never delete",
        "do not delete",
        "must keep",
        "keep-list",
        "keep list",
    )
    _LEARN_HINTS = ("learn", "new skill", "create skill", "repeat", "habit")
    _STALE_HINTS = ("stale", "outdated", "wrong", "no longer")
    _UNLEARN_HINTS = ("unlearn", "retire", "remove", "delete")

    # ─── Block 2: Module Contract ─────────────
    def scan_memory(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
    ) -> MemoryReport:
        """Read ``$GROK_HOME/memory-v2`` topics and observations.
        A monthly (30-day) window is hardcoded — only memory items modified
        within the last 30 days are kept. ``since_last`` and ``days`` are
        removed; nothing is configurable by the caller. Never edits memory
        files.
        """
        grok_home_path = os.path.abspath(os.path.expanduser(grok_home))
        memory_root = os.path.join(grok_home_path, "memory-v2")
        run_dir_path = os.path.abspath(run_dir)
        clear_run_dir(run_dir_path, action="memory")
        os.makedirs(run_dir_path, exist_ok=True)
        # Hardcoded 30-day window: keep memory items mtime >= now - 30 days.
        cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=30)
        topics: list[MemoryTopicRow] = []
        observations: list[MemoryObservationRow] = []
        keep_skills: list[str] = []

        def keep_ok(path: str) -> bool:
            try:
                mtime = dt.datetime.fromtimestamp(os.path.getmtime(path), tz=dt.UTC)
            except OSError:
                return True
            return mtime >= cutoff

        topic_roots = []
        if os.path.isdir(os.path.join(memory_root, "global", "topics")):
            topic_roots.append(
                ("global", os.path.join(memory_root, "global", "topics"))
            )
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
                        h in ln_low
                        for h in (
                            *self._KEEP_HINTS,
                            *self._LEARN_HINTS,
                            *self._STALE_HINTS,
                            *self._UNLEARN_HINTS,
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
        with open(os.path.join(run_dir_path, "memory.json"), "w", encoding="utf-8") as f:
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
            front[key] = [
                x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()
            ]
        elif val.startswith('"') and val.endswith('"'):
            front[key] = val[1:-1]
        else:
            front[key] = val
    return front, body
