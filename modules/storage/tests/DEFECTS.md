# DEFECTS — storage module defect log

| # | ID | Summary | Severity | Assigned | Status |
|---|----|---------|----------|----------|--------|
| 1 | STORAGE-001 | `contract_storage_protocol.py` defined a duplicate `ISkillsStorageAggregate` with a conflicting `execute(verb, root)` signature while `contract_storage_aggregate.py` defines `execute(request: StorageRequest)`, creating a dead, conflicting contract. | Medium | storage | fixed |

---

## STORAGE-001 — Duplicate conflicting `ISkillsStorageAggregate`

**Reproduction steps:**
1. Inspect `shared/src/storage/contract_storage_protocol.py` vs `shared/src/storage/contract_storage_aggregate.py`.
2. Observe two `ISkillsStorageAggregate` definitions with different `execute()` signatures.

**Expected:** Single source of truth; the agent implements the `StorageRequest` variant from `contract_storage_aggregate.py`.

**Actual (before fix):** `contract_storage_protocol.py` declared `execute(self, verb: StorageVerb, root: SkillsRoot | None = None)` — dead and conflicting with the implemented `execute(self, request: StorageRequest)`.

**Fix:** Removed the duplicate `ISkillsStorageAggregate` from `contract_storage_protocol.py`.

**Status:** fixed
