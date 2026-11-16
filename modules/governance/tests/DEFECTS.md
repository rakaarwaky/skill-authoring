# DEFECTS — governance module defect log

| # | ID | Summary | Severity | Assigned | Status |
|---|----|---------|----------|----------|--------|
| 1 | GOVERNANCE-001 | `ISkillsPinerProtocol.pin()`/`unpin()` declared return type `GovernanceResponse`, but the capabilities return `dict`, producing an unstructured `str(result)` message in the governance agent. | Medium | governance | fixed |

---

## GOVERNANCE-001 — Protocol/impl return type mismatch

**Reproduction steps:**
1. Inspect `ISkillsPinerProtocol.pin()` signature vs `SkillsPiner.pin()` implementation.
2. Call `sac pin <skill>` and inspect the message.

**Expected:** Contract matches implementation; message is structured.

**Actual (before fix):** Protocol declared `GovernanceResponse` return but capabilities returned plain `dict`; `str(result)` on the dict produced `"{'skill': 'x', 'pinned': True}"`.

**Fix:** Changed protocol method signatures to return `dict`, matching the implementations.

**Status:** fixed
