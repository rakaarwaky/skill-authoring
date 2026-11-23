"""Phrase-scan trace capability (AES capabilities layer).

Produces ``phrase.json`` run-dir artifact from session records. Reads session
records already written to ``run_dir/sessions/`` by ``scan_sessions`` and mines
repeated exact prompts, stems, and instruction lines.
Depends only on the trace contract + taxonomy from the shared kernel plus the
shared run-dir clearing utility. Never imports other capabilities (AES201).
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict

from shared.src.observability.contract_observability_protocol import (
    ISkillsPhraseProtocol,
)
from shared.src.observability.taxonomy_observability_vo import (
    GrokHome,
    PhraseRow,
    PhrasesReport,
    TraceRunDir,
)
from shared.src.observability.utility_observability_run_dir import clear_run_dir

__all__ = ["SkillsObservabilityPhrase"]


# ─── Block 1: Module Declaration ──────────────
class SkillsObservabilityPhrase(ISkillsPhraseProtocol):
    """Mines repeated phrases from session records; writes phrase.json.

    Implements exactly one protocol (ISkillsPhraseProtocol) with one public
    method (build_phrases). No stubs, no NotImplementedError.
    """

    _MIN_PHRASE_LEN = 12
    _MIN_LINE_WORDS = 5
    _MIN_LINE_CHARS = 24
    _EXACT_MIN_SESSIONS = 2
    _STEM_MIN_SESSIONS = 3
    _LINE_MIN_SESSIONS = 3
    _TOP = 60
    SLASH_RE = re.compile(r"/[a-z0-9-]+(\s+\S+){0,3}")
    SLASH_ONLY = re.compile(r"/[a-z0-9-]+(\s+\S+){0,3}$")

    # ─── Block 2: Module Contract ─────────────
    def build_phrases(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
    ) -> PhrasesReport:
        """Read session records from ``run_dir``; mine repeated phrases; write ``phrase.json``.

        Clearing ownership: clears ONLY ``phrase.json`` via
        ``clear_run_dir(run_dir, action="phrase")``. It never clears ``sessions/``
        or ``manifest.json`` — those are owned by ``scan_sessions`` (which already
        ran). Re-wiping ``sessions/`` here would delete the records this capability
        is about to read.
        """
        # Clears phrase.json only; never sessions/ or manifest.json.
        clear_run_dir(run_dir, action="phrase")
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
                    if self.SLASH_RE.fullmatch(stripped) or self.SLASH_ONLY.fullmatch(
                        n
                    ):
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
            exact_prompts=self._top(exact, min_sessions),
            stems=self._top(stems, self._STEM_MIN_SESSIONS),
            repeated_instruction_lines=self._top(lines, self._LINE_MIN_SESSIONS),
        )
        _write_phrase(run_dir, report)
        return report

    # ─── Block 3: Module Helpers ─────────
    @staticmethod
    def _top(data: dict, min_count: int) -> tuple[PhraseRow, ...]:
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
        return tuple(rows[: SkillsObservabilityPhrase._TOP])


def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


def _write_phrase(run_dir: str, report: PhrasesReport) -> None:
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
    with open(os.path.join(run_dir, "phrase.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
