# DEFECTS — observability module defect log

| # | ID | Summary | Severity | Assigned | Status |
|---|----|---------|----------|----------|--------|
| 1 | OBSERVABILITY-001 | `SkillsResult` had no `phrases_exact`, `phrases_stems`, `phrases_lines` fields, yet `ObservabilityAgent._execute_phrases` constructed `SkillsResult(phrases_exact=..., ...)` and `_render_phrases` read them — `sac phrases` crashed at runtime. | High | observability | fixed |
| 2 | OBSERVABILITY-002 | `SkillsMcpAdapter.execute_tool()` returned `result.message or str(result)`, so an empty message produced an unhelpful dataclass dump for MCP clients. | Low | observability | fixed |

---

## OBSERVABILITY-001 — `SkillsResult` lacks phrases fields (crash on `sac phrases`)

**Reproduction steps:**
1. Run `sac phrases`.
2. Observe whether the command crashes.

**Expected:** `SkillsResult` carries `phrases_exact`, `phrases_stems`, `phrases_lines`; `_render_phrases` reads them cleanly.

**Actual (before fix):** `TypeError` because frozen dataclass rejected unknown keyword arguments; then `AttributeError` when reading `result.phrases_exact`.

**Fix:** Added `phrases_exact`, `phrases_stems`, `phrases_lines` fields (typed `tuple[PhraseRow, ...]`, defaulting to empty tuples) to `SkillsResult`, importing `PhraseRow` under `TYPE_CHECKING`.

**Status:** fixed

---

## OBSERVABILITY-002 — Empty `message` yields unhelpful MCP string

**Reproduction steps:**
1. Call an MCP tool whose result has an empty `message`.
2. Inspect the text returned to the MCP client.

**Expected:** A meaningful client-facing string like `"{op}: exit {exit_code}"`.

**Actual (before fix):** `str(result)` dumped the whole dataclass (e.g. `SkillsResult(ok=True, op=..., exit_code=0, message='', ...)`).

**Fix:** Changed `execute_tool` fallback to `result.message or f"{result.op}: exit {result.exit_code}"`.

**Status:** fixed
