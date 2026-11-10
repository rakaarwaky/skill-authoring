# DEFECTS — maintenance module defect log

| # | ID | Summary | Severity | Assigned | Status |
|---|----|---------|----------|----------|--------|
| 1 | MAINTENANCE-001 | `_render_prune()` string-matched `"'dry_run': True"` / `'"dry_run": true"'` in `result.message` to detect dry-run, but `SkillsPrune.prune()` never included `dry_run` in its report dict, so `[DRY-RUN]` was never emitted. | Medium | maintenance | fixed |
| 2 | MAINTENANCE-002 | `SkillsPurge.purge()` called `shutil.rmtree(skill_dir, ignore_errors=True)`, silently swallowing `OSError` and reporting `{"purged": True}` even when deletion partially or fully failed. | High | maintenance | fixed |

---

## MAINTENANCE-001 — Dry-run state never emitted in `_render_prune()`

**Reproduction steps:**
1. Run `sac prune --days N --apply` (dry-run mode) and observe whether `[DRY-RUN]` prefix appears.

**Expected:** `[DRY-RUN] prune — ...` when dry-run is active.

**Actual (before fix):** `[OK] prune — ...` even in dry-run, because the string-match on `result.message` never matched.

**Fix:** Included `dry_run` in the prune report dict returned by `SkillsPrune.prune()`.

**Status:** fixed

---

## MAINTENANCE-002 — `shutil.rmtree(ignore_errors=True)` swallowed deletion errors

**Reproduction steps:**
1. Delete an archived skill whose directory has read-only files.
2. Inspect whether `{"purged": True}` is returned despite partial failure.

**Expected:** `OSError` propagates so the agent surfaces a controlled failure.

**Actual (before fix):** `ignore_errors=True` silently swallowed errors; caller always got `{"purged": True}`.

**Fix:** Removed `ignore_errors=True` so `OSError` propagates.

**Status:** fixed
