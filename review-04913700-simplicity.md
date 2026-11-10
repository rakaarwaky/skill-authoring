# Simplicity Review — Skill Modules Review Fixes

Review scope: over-engineering and unnecessary complexity only. Correctness, security, and test coverage are out of scope.

Format: severity (`bug`/`suggestion`/`nit`), file:line, description, suggestion, Status: open.

---

## 1. Redundant `default_pack_root` wrapper in storage layer

**severity:** suggestion — `shrink` / `yagni`
**file:** `modules/shared/src/storage/utility_skill_pack.py:28-33`
**description:** `utility_skill_pack.py` defines its own `default_pack_root()` whose body is identical to the one already in `utility_common_skills.py` (`modules/shared/src/common/utility_common_skills.py:132-134`). Both do nothing but call `find_repo_root()`. The storage-layer wrapper adds an indirection layer with no behavioral difference. Two callers (`capabilities_discovery_reader.py`, `capabilities_discovery_lister.py`) import it from the storage package instead of the common package, perpetuating the duplicate.
**suggestion:** Delete `default_pack_root()` from `utility_skill_pack.py` (and its `__all__` / `__init__.py` re-exports) and have the two discovery callers import `default_pack_root` from `shared.src.common.utility_common_skills` directly, matching the other 12+ call sites.
**Status:** open

---

## 2. `dry_run` added to prune report but never consumed by its only caller

**severity:** nit — `shrink`
**file:** `modules/cli/src/surface_skills_command.py:357-359`; `modules/maintenance/src/capabilities_skills_prune.py:89`
**description:** Architect-6/QA-4 added `"dry_run": dry_run` to the prune report dict, but `_render_prune()` still detects dry-run via brittle string-matching on `result.message`:
```python
dry_run = False
if "'dry_run': True" in str(result.message) or '"dry_run": true' in str(result.message):
    dry_run = True
```
The new `dry_run` field is written but never read by its single consumer. This is a half-applied fix: an abstraction added to the report while the brittle string-parsing remains, so the field is speculative/dead for current callers.
**suggestion:** Either consume `report["dry_run"]` in `_render_prune` (e.g. pass it through `result.records` or `result.message` structure) and drop the string-matching, or remove the `dry_run` key from the report if the renderer will not use it. Do not carry an unconsumed field.
**Status:** open

---

## 3. Speculative `parents[7]` fallback in `find_repo_root`

**severity:** suggestion — `yagni`
**file:** `modules/shared/src/common/utility_common_skills.py:57-59`
**description:** `find_repo_root()` walks up from `__file__` looking for `.git` or `pyproject.toml`, then falls back to `Path(__file__).resolve().parents[7]` if no marker exists. The summary itself describes this as "preserv[ing] the previous default behaviour for relocated trees without markers." Keeping the old depth-based resolution as a fallback adds a second, fragile code path for a scenario the marker-based approach is meant to replace. If marker discovery is canonical, the fallback is speculative complexity.
**suggestion:** Remove the `parents[7]` fallback; let `find_repo_root()` raise or return a clear sentinel when no marker is found, rather than silently falling back to a depth-based guess that can break on tree relocation.
**Status:** open

---

## 4. Import solely for side effect, then discard

**severity:** nit
**file:** `modules/root_cli_entry.py:16,21-23`
**description:** `root_cli_entry.py` imports `_REPO_ROOT` from `utility_path_bootstrap` solely to trigger the module-level `sys.path` insertion side effect, then immediately discards it with `_ = _REPO_ROOT`. An explanatory comment was added (Backend-5/QA-8), but the import-for-side-effect-then-discard pattern remains. It is a minor smell: the import's only purpose is side effect, and the discard line is noise.
**suggestion:** Acceptable as a documented side-effect import; if simplifying, move the path-bootstrap call into an explicit function (e.g. `bootstrap_ns_roots()`) called at entry instead of relying on import-time side effects plus a discard. Low priority.
**Status:** open

---

## Not flagged (used in production, not over-engineered)

- `phrases_exact` / `phrases_stems` / `phrases_lines` on `SkillsResult` (`taxonomy_design_response.py:79-81`): populated by `ObservabilityAgent._execute_phrases` (`agent_observability_orchestrator.py:198-200`) and consumed by `_render_phrases` (`surface_skills_command.py:183-230`) plus a unit test. Real usage, not dead code.
- `assert_within_root` calls in `create_skill` (`capabilities_skills_creator.py:69,73,96`): both plan-time and apply-time checks are intentional defense-in-depth per the existing pattern in `create_category`; not speculative.
- `ValueError` added to `_mutate_skill` exception tuple (`agent_design_orchestrator.py:96`): matches governance agent's existing tuple; not a new abstraction.
- `--compact` removal from ledger parser (`surface_skills_command.py`): removes a no-op flag; simplification, not bloat.
