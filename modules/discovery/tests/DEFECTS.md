# DEFECTS — discovery module defect log

| # | ID | Summary | Severity | Assigned | Status |
|---|----|---------|----------|----------|--------|
| 1 | DISCOVERY-001 | `_execute_discover` empty-query guard returned `exit_code=1`; contract requires exit 2. | High | discovery | fixed |
| 2 | DISCOVERY-002 | `execute()` coerced `limit=int(...)` directly, letting a non-numeric flag raise uncaught `ValueError`. | Medium | discovery | fixed |
| 3 | DISCOVERY-003 | `list_skills_json` emitted `"source"` naming the construction-time pack root instead of the actually-walked root. | Medium | discovery | fixed |
| 4 | DISCOVERY-004 | `show_skill` treated `if exact:` as truthy, so multiple skills sharing a frontmatter name returned the first instead of `None` (ambiguous match). | Medium | discovery | fixed |
| 5 | DISCOVERY-005 | `root_discovery_container.py` used bare imports; module was dead code and `src/` was not a package. Removed. | Low | discovery | fixed |
| 6 | DISCOVERY-006 | `SkillsDiscoveryAgent.show_skill` lacked a `SkillContent | None` return annotation. | Low | discovery | fixed |

---

## DISCOVERY-001 — Empty discover query returns wrong exit code

**Reproduction steps:**
1. Build a real skills pack with at least one skill.
2. Call `agent.execute(DiscoveryRequest(verb=DiscoveryVerb.DISCOVER, query=DiscoveryQuery(""), root=DiscoveryRoot(pack_root)))`.
3. Observe `result.exit_code`.

**Environment:** `modules/discovery/src/agent_discovery_orchestrator.py`, Python 3.12+, uv.

**Expected:** `ok is False`, `exit_code == 2`, `"Query required" in message` (FR-discovery-004: empty query raises usage error, exit 2).

**Actual (before fix):** `exit_code == 1`.

**Fix:** Changed `_execute_discover`'s empty-query guard from `exit_code=1` to `exit_code=2`.

**Status:** fixed

---

## DISCOVERY-002 — Invalid limit flag raises uncaught ValueError

**Reproduction steps:**
1. Call `agent.execute(DiscoveryRequest(verb=DiscoveryVerb.DISCOVER, query=DiscoveryQuery("fetch"), flags={"limit": "abc"}, root=...))`.
2. Observe whether `ValueError` escapes.

**Environment:** `modules/discovery/src/agent_discovery_orchestrator.py`, Python 3.12+, uv.

**Expected:** `ok is False`, `exit_code == 2`, `"Invalid limit" in message` — no exception escapes.

**Actual (before fix):** `ValueError` from `int("abc")` escaped uncaught.

**Fix:** Validate the limit string before coercion; return a `DiscoveryResponse` with `ok=False`, `exit_code=2`, and a usage message on invalid input.

**Status:** fixed

---

## DISCOVERY-003 — `list_skills_json` source names construction root

**Reproduction steps:**
1. Construct `SkillsLister(construction_root)`.
2. Call `lister.list_skills_json(root=other_root)`.
3. Inspect `payload["skills"][0]["source"]`.

**Environment:** `modules/discovery/src/capabilities_discovery_lister.py`, Python 3.12+, uv.

**Expected:** `"source"` equals `str(other_root)` (the actually-walked root).

**Actual (before fix):** `"source"` equaled `str(self._root)` (construction-time pack root).

**Fix:** Changed `"source": str(self._root)` to `"source": str(skills_root)`.

**Status:** fixed

---

## DISCOVERY-004 — Ambiguous exact match returns first skill instead of None

**Reproduction steps:**
1. Create two skills both with frontmatter `name: fetch` under different categories.
2. Call `reader.show_skill(DiscoveryQuery("fetch"), root=...)`.
3. Observe the return value.

**Environment:** `modules/discovery/src/capabilities_discovery_reader.py`, Python 3.12+, uv.

**Expected:** `None` (ambiguous match — no silent pick).

**Actual (before fix):** Returned the first matching skill's content because `if exact:` was truthy for any non-empty list.

**Fix:** Changed `if exact:` to `if len(exact) == 1:`.

**Status:** fixed

---

## DISCOVERY-005 — Dead code: `root_discovery_container.py` and `src/__init__.py`

**Reproduction steps:**
1. Inspect `modules/discovery/src/` — `root_discovery_container.py` used bare imports and `src/` was not importable as a package; tests inject `discovery/src` onto `sys.path` directly.
2. Confirm no consumer imports from `src.root_discovery_container`.

**Environment:** `modules/discovery/src/root_discovery_container.py`, `modules/discovery/src/__init__.py`, Python 3.12+, uv.

**Expected:** No dead code; `src/` not a package; no orphaned `__init__.py`.

**Actual (before fix):** Dead container module and a vestigial `__init__.py` existed.

**Fix:** Deleted `root_discovery_container.py` and `src/__init__.py`.

**Status:** fixed

---

## DISCOVERY-006 — `show_skill` missing return type annotation

**Reproduction steps:**
1. Inspect `SkillsDiscoveryAgent.show_skill` signature in `modules/discovery/src/agent_discovery_orchestrator.py`.
2. Confirm return annotation is `SkillContent | None`.

**Environment:** `modules/discovery/src/agent_discovery_orchestrator.py`, Python 3.12+, uv.

**Expected:** Return annotation `-> SkillContent | None`.

**Actual (before fix):** No return annotation declared.

**Fix:** Added `-> SkillContent | None` to `SkillsDiscoveryAgent.show_skill`.

**Status:** fixed
