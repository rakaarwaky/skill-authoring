# Simplicity Review — Skill Modules Review Fixes (Re-review)

Review scope: over-engineering and unnecessary complexity only. Correctness, security, and test coverage are out of scope.

Format: severity (`bug`/`suggestion`/`nit`), file:line, description, suggestion, Status: open.

---

## 1. `dry_run` value travels through a string round-trip via `ast.literal_eval`

**severity:** suggestion — `shrink`
**file:** `modules/cli/src/surface_skills_command.py:40,356-365`; `modules/maintenance/src/agent_maintenance_orchestrator.py:119-122`
**description:** `SkillsPrune.prune()` returns a dict containing the native Python bool `dry_run`. The maintenance agent then stringifies it with `message=str(report)` (`agent_maintenance_orchestrator.py:122`), and `_render_prune` recovers it with `ast.literal_eval(result.message)` (`surface_skills_command.py:359-361`). This is a dict → `str()` → `ast.literal_eval` → dict round-trip solely to read one boolean that was already available as a Python native type before stringification. The fix also adds `import ast` (line 40) to the file for this single use. Replacing fragile substring matching with `literal_eval` is more correct, but the string round-trip itself is unnecessary complexity: the boolean was structured data before being stringified and is being re-parsed from a string.
**suggestion:** Avoid the string round-trip. Either carry `dry_run` through a structured channel on `SkillsResult` (e.g. a dedicated field or via `records`), or set `message` in the agent to a form that doesn't require re-parsing a stringified dict just to extract one bool. Remove the now-single-use `import ast` if no other consumer emerges.
**Status:** open

---

## 2. Import solely for side effect, then discard

**severity:** nit
**file:** `modules/root_cli_entry.py:16,21-23`
**description:** `root_cli_entry.py` imports `_REPO_ROOT` from `utility_path_bootstrap` solely to trigger the module-level `sys.path` insertion side effect, then immediately discards it with `_ = _REPO_ROOT`. An explanatory comment was added, but the import-for-side-effect-then-discard pattern remains. It is a minor smell: the import's only purpose is side effect, and the discard line is noise. The implementer marked this wontfix (documented, intentional under AES504, outside `modules/` scope), but it remains an instance of unnecessary complexity in the changed code.
**suggestion:** Acceptable as a documented side-effect import; if simplifying, move the path-bootstrap call into an explicit function (e.g. `bootstrap_ns_roots()`) called at entry instead of relying on import-time side effects plus a discard. Low priority.
**Status:** open

---

## Not flagged (used in production, not over-engineered)

- `phrases_exact` / `phrases_stems` / `phrases_lines` on `SkillsResult` (`taxonomy_design_response.py:79-81`): populated by `ObservabilityAgent._execute_phrases` (`agent_observability_orchestrator.py:198-200`) and consumed by `_render_phrases` (`surface_skills_command.py:183-230`) plus a unit test. Real usage, not dead code.
- `assert_within_root` calls in `create_skill` (`capabilities_skills_creator.py:69,73,96`): both plan-time and apply-time checks are intentional defense-in-depth per the existing pattern in `create_category`; not speculative.
- `ValueError` added to `_mutate_skill` exception tuple (`agent_design_orchestrator.py:96`): matches governance agent's existing tuple; not a new abstraction.
- `--compact` removal from ledger parser and usage banner (`surface_skills_command.py`): removes a no-op flag; simplification, not bloat. MCP `_flags` compact block also removed (`surface_mcp_command.py`). Confirmed fixed.

## Previously flagged, now fixed (do not re-list)

- **Redundant `default_pack_root` wrapper** in `utility_skill_pack.py`: deleted; discovery callers now import from `shared.src.common.utility_common_skills`. Confirmed fixed.
- **Speculative `parents[7]` fallback** in `find_repo_root`: removed; function now raises `SkillsUsageError` when no marker exists. Confirmed fixed.
