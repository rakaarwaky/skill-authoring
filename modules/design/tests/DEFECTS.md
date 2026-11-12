# DEFECTS — design module defect log

| # | ID | Summary | Severity | Assigned | Status |
|---|----|---------|----------|----------|--------|
| 1 | DESIGN-001 | `SkillsCreator.create_skill()` skipped `assert_within_root`, enabling path traversal via `../` in `category` or `skill`. | High | design | fixed |
| 2 | DESIGN-002 | `SkillsDesignAgent._mutate_skill()` caught only `(OSError, SkillsError)`, letting plain `ValueError` from the adopter/locker/piner escape as an unhandled traceback instead of a controlled `SkillsResult` exit code 2. | High | design | fixed |
| 3 | DESIGN-003 | `_execute_lint()` derived exit code from `report.unfiltered_issue_count` instead of `report.issue_count`, so exit code and rendered output disagreed under `--category`. | Medium | design | fixed |
| 4 | DESIGN-004 | `_execute_run()` assigned `report.get("applied", ())` (a `list[dict]`) to `SkillsResult.records` typed `tuple[SkillRecord, ...]`, a typed-contract violation. | Medium | design | fixed |

---

## DESIGN-001 — Path traversal in `create_skill()`

**Reproduction steps:**
1. Call `creator.create_skill(skill="evil", category="../outside", ...)` with `apply=True`.
2. Observe that `SKILL.md` is written outside the skills root.

**Expected:** `SkillsUsageError` raised because the destination escapes the skills root.

**Actual (before fix):** File written outside the pack with no containment check.

**Fix:** Added `assert_within_root(directory, skills_root)` at plan time and `assert_within_root(skill_md, skills_root)` before `write_text`, mirroring `create_category()`.

**Status:** fixed

---

## DESIGN-002 — `_mutate_skill` missing `ValueError` catch

**Reproduction steps:**
1. Call the design agent for an op whose capability raises `ValueError` (e.g. `SkillsAdopter.adopt()` on a missing skill).
2. Observe whether `ValueError` escapes `execute()`.

**Expected:** Controlled `SkillsResult` with `ok=False`, `exit_code=2`, message naming the failure.

**Actual (before fix):** `ValueError` propagated past `_mutate_skill` and past `execute()`'s `except SkillsError`, producing an unhandled traceback.

**Fix:** Added `ValueError` to the exception tuple in `_mutate_skill()`, matching the governance agent's `_mutate_skill()`.

**Status:** fixed

---

## DESIGN-003 — Lint exit code / rendered output disagreement

**Reproduction steps:**
1. Run `sac lint --category X` where issues exist only in other categories.
2. Compare exit code vs rendered output.

**Expected:** Exit code 0 ("clean") matching the rendered "No issues in category 'X'".

**Actual (before fix):** Exit code 1 (issues found) despite rendering "No issues in category 'X'".

**Fix:** Derived the exit code from `report.issue_count` (the filtered count actually rendered).

**Status:** fixed

---

## DESIGN-004 — `records` typed-contract violation in `_execute_run`

**Reproduction steps:**
1. Call `sac run` and inspect `result.records`.
2. Access `rec.name` on a record.

**Expected:** Each record is a `SkillRecord` with a `.name` attribute.

**Actual (before fix):** Each record was a plain `dict` from `report.get("applied", ())`, so `.name` raised `AttributeError`.

**Fix:** Removed the `records=` assignment from `_execute_run`; `message` now carries the report text.

**Status:** fixed
