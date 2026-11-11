# FRD — governance

## Feature Overview

The governance feature owns the skill-lifecycle flag verbs: lock,
unlock, pin, unpin, and move. A governance agent
(`SkillsGovernanceAgent`) implements the governance-domain aggregate
contract (`ISkillsGovernanceAggregate`) and routes each `SkillsOp` to
the capability protocol that owns the verb — the locker toggles the
`locked` sidecar flag, the piner toggles the `pinned` flag, and the
mover plans and applies cross-category moves. The agent orchestrates
only: it holds no I/O, no domain data, and no computation. Every
filesystem operation happens inside a capability; the composition root
injects the concrete capabilities into the agent through the three
protocol seams (`ISkillsLockerProtocol`, `ISkillsPinerProtocol`,
`ISkillsMoverProtocol`).

The feature is composed with the design, discovery, maintenance,
observability, storage, and traces agents into a single
`ISkillsAggregate` facade that the CLI surface receives.

## Functional Requirements

### FR-GOVERNANCE-001: Locker

**Description:** Toggle the `locked` flag on a skill's sidecar record.
A locked skill is exempt from prune and archive sweeps; an unlocked
skill is fair game again.

#### Business Logic — Locker

- Lock sets `locked=True` in the skill's sidecar; unlock sets
  `locked=False`.
- The sidecar is written in place under the skill directory; no other
  skill file is touched.
- A missing skill directory is a usage error naming the skill.

#### Edge Cases — Locker

- Skill directory not found → typed error naming the skill.
- Capability unwired → typed error before any work begins.

#### Technical Specification — Locker

| Aspect   | Detail                                               |
| -------- | ---------------------------------------------------- |
| Input    | skill name; optional pack-root override              |
| Output   | `GovernanceResponse` with ok=True, verb=lock/unlock, |
|          | message carrying the sidecar write result            |
| Protocol | `ISkillsLockerProtocol`                              |
| Method   | `lock(skill, root)` / `unlock(skill, root)`          |
| Event    | —                                                    |
| Error    | missing skill, unwired capability → typed error      |

#### Test — Locker

| When Action                 | Then Observable Result         |
| --------------------------- | ------------------------------ |
| `sac skills lock <skill>`   | sidecar `locked=True`, exit 0  |
| `sac skills unlock <skill>` | sidecar `locked=False`, exit 0 |
| `sac skills lock <unknown>` | exit 2 naming the skill        |

#### Metric — Locker

| Target Metric | Value                                                  |
| ------------- | ------------------------------------------------------ |
| Flag fidelity | a lock/unlock pair returns the sidecar to its original |
|               | state                                                  |

### FR-GOVERNANCE-002: Mover

**Description:** Plan or apply a move of a skill directory to another
category under the same pack root. The move is dry-run by default;
`--apply` writes.

#### Business Logic — Mover

- Plan resolves the source skill directory, validates the target
  category name, and asserts the destination stays inside the pack
  root; the plan takes no action.
- Apply re-checks containment before writing, so a symlink created
  between plan and apply fails closed.
- A move into the skill's current category is a no-op plan with
  `already_in_category=True`.
- A destination that already exists is a conflict error.

#### Edge Cases — Mover

- Target category does not exist → usage error naming the category.
- Destination already exists → conflict error.
- Missing `--target` flag → usage error.
- Capability unwired → typed error before any work begins.

#### Technical Specification — Mover

| Aspect   | Detail                                                 |
| -------- | ------------------------------------------------------ |
| Input    | skill name, target category, pack root, `--apply` flag |
| Output   | `GovernanceResponse` with `MutationPlan` (dry-run) or  |
|          | `MutationOutcome` (apply)                              |
| Protocol | `ISkillsMoverProtocol`                                 |
| Method   | `plan_move(skill, target, root)` / `apply_move(plan)`  |
| Event    | —                                                      |
| Error    | missing target, unknown category, conflict, unwired    |
|          | capability → typed error                               |

#### Test — Mover

| When Action                                  | Then Observable Result        |
|----------------------------------------------|-------------------------------|
| `sac skills move <skill> --target B`         | plan reports destination,     |
|                                              |   none                        |
| `sac skills move <skill> --target B --apply` | skill directory under B, exit |
|                                              |   0                           |
| `sac skills move <skill> --target C`         | exit 2 naming C               |

#### Metric — Mover

| Target Metric         | Value                                 |
| --------------------- | ------------------------------------- |
| Containment invariant | no apply writes outside the pack root |

### FR-GOVERNANCE-003: Pinner

**Description:** Toggle the `pinned` flag on a skill's sidecar record.
A pinned skill is exempt from automatic lifecycle transitions
(archive-on-idle); an unpinned skill is subject to them.

#### Business Logic — Pinner

- Pin sets `pinned=True`; unpin sets `pinned=False`.
- The pin flag is read by the telemetry auto-transition pass; it does
  not affect lock, move, or archive on its own.

#### Edge Cases — Pinner

- Skill directory not found → typed error naming the skill.
- Capability unwired → typed error before any work begins.

#### Technical Specification — Pinner

| Aspect   | Detail                                             |
| -------- | -------------------------------------------------- |
| Input    | skill name; optional pack-root override            |
| Output   | `GovernanceResponse` with ok=True, verb=pin/unpin, |
|          | message carrying the sidecar write result          |
| Protocol | `ISkillsPinerProtocol`                             |
| Method   | `pin(skill, root)` / `unpin(skill, root)`          |
| Event    | —                                                  |
| Error    | missing skill, unwired capability → typed error    |

#### Test — Pinner

| When Action                | Then Observable Result         |
| -------------------------- | ------------------------------ |
| `sac skills pin <skill>`   | sidecar `pinned=True`, exit 0  |
| `sac skills unpin <skill>` | sidecar `pinned=False`, exit 0 |

## Public Interface

| Aspect    | Detail                                               |
| --------- | ---------------------------------------------------- |
| Agent     | `SkillsGovernanceAgent`                              |
| Aggregate | `ISkillsGovernanceAggregate`                         |
| Method    | `execute(request)`                                   |
| Request   | `SkillsRequest` (op, query, root, flags)             |
| Response  | `SkillsResult` (message, move_plan, root, exit_code) |

## Reference

| Artifact     | Purpose                                  |
| ------------ | ---------------------------------------- |
| PRD          | [PRD.md](../../PRD.md)                   |
| FRD          | [FRD.md](FRD.md)                         |
| Roadmap      | [ROADMAP.md](../../ROADMAP.md)           |
| Architecture | [ARCHITECTURE.md](../../ARCHITECTURE.md) |
