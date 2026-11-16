# FRD — maintenance

## Feature Overview

The maintenance feature sits in the agent layer and is called by the surface
and root CLI through the `ISkillsMaintenanceAggregate` contract. It orchestrates
four capabilities — prune, runner, piner, mover — and routes each maintenance
op to the matching capability through a single `execute` entry point. The agent
performs no filesystem I/O; every archive, purge, transition, pin, and move is
delegated to a capability. Archive and restore of individual skills belong to
the [storage module](../storage/FRD.md), which owns its own
`ISkillsArchiverProtocol` / `ISkillsRestoreProtocol` seams.

## Functional Requirements

### FR-maintenance-001: Prune

**Description:** `SkillsMaintenanceAgent.execute(request)` shall route the
`PRUNE` maintenance op to the prune capability and return a typed
`MaintenanceResponse` to the caller. The prune capability archives idle skills
past a configurable days threshold (default 30), then purges archived skills
past a configurable archive TTL (default 60) in one pass. The maintenance
aggregate contract (`ISkillsMaintenanceAggregate`) is the single entry point the
surface and root CLI use; no caller reaches the prune capability directly. The
agent performs no filesystem I/O; the prune capability owns all I/O.

#### Business Logic

- On `PRUNE`, the agent shall read a `days` threshold flag (idle → archive,
  default 30) and a `purge_days` threshold flag (archived → purge, default 60).
- On `PRUNE` with `dry_run=True`, the agent shall return a plan without
  archiving or purging any skills.
- Pinned skills and cron-referenced skills shall never be archived.
- Purge shall never delete a skill still active in the pack; it only removes
  archived skills whose archive age exceeds `purge_days`.
- An op string that is not one of the maintenance ops shall produce a response
  with `USAGE_ERROR` exit code and a message naming the unknown op.
- A `SkillsError` raised by the prune capability shall be caught by the agent
  and mapped to a response carrying the error's exit code and message.
- A missing prune capability at construction shall raise a root-level error at
  the first `PRUNE` call, not at construction.

#### Edge Cases

- A `PRUNE` request with `days` below 1 shall produce a `MaintenanceResponse`
  with `ok=False`, exit code `1`, and a message naming the invalid threshold.
- A `PRUNE` request with `purge_days=0` shall skip the purge pass and archive
  only.
- An unknown op string shall produce a response with `USAGE_ERROR` exit code
  and a message naming the unknown op.
- A `SkillsError` raised by the prune capability shall be caught and mapped to
  a response with the error's exit code and message.

#### Technical Specification

| Aspect       | Detail                                                                 |
| ------------ | ---------------------------------------------------------------------- |
| **Input**    | `MaintenanceRequest` (verb, skill, flags, root). Source: surface / root CLI. |
| **Output**   | `MaintenanceResponse` (ok, verb, exit_code, message, records). Destination: surface / root CLI. |
| **Protocol** | `ISkillsPrunerProtocol`                                                |
| **Method**   | `execute` → `prune`                                                    |
| **Event**    | None                                                                   |
| **Error**    | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2                           |

#### Test

| Context                               | When Action                                   | Then Observable Result                                                     |
| ------------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------- |
| A `PRUNE` request that finds idle skills | `execute` with `verb=PRUNE`                | `MaintenanceResponse` with `ok=True`, archived records populated, exit code `CLEAN` |
| A `PRUNE` request that finds old archives | `execute` with `verb=PRUNE`              | `MaintenanceResponse` with `ok=True`, purged records populated, exit code `CLEAN` |
| A `PRUNE` request with `dry_run=True` | `execute` with `verb=PRUNE` and `dry_run=True` | Plan with archived/purged lists; no filesystem write occurs                |
| A `PRUNE` request with `purge_days=0` | `execute` with `verb=PRUNE` and `purge_days=0` | Only the archive pass runs; no purge occurs                                |
| A `PRUNE` request with `days` below 1 | `execute` with `verb=PRUNE` and `days=0`     | `MaintenanceResponse` with `ok=False`, exit code `1`, message naming the invalid threshold |

#### Metric

| Target Metric                                   | Value |
| ----------------------------------------------- | ----- |
| Dispatch p95 latency                            | 5 ms  |
| Unknown-op rejection rate                       | 100 % |
| Unhandled exception escape rate                 | 0 %   |
| Direct capability call rate from outside the agent | 0 % |

### FR-maintenance-002: Runner

**Description:** `SkillsMaintenanceAgent.execute(request)` shall route the
`RUN`, `PAUSE`, and `RESUME` maintenance ops to the runner capability and
return a typed `MaintenanceResponse` to the caller. The runner capability
applies automatic lifecycle transitions, pauses, and resumes them via
`ISkillsRunnerProtocol`.

#### Business Logic

- On `RUN`, the agent shall apply automatic lifecycle transitions across the
  pack via `apply_automatic_transitions` and return `CLEAN`.
- On `PAUSE`, the agent shall pause lifecycle transitions via `pause` and
  return `CLEAN`.
- On `RESUME`, the agent shall resume lifecycle transitions via `resume` and
  return `CLEAN`.
- A `SkillsError` raised by the runner capability shall be caught by the agent
  and mapped to a response carrying the error's exit code and message.

#### Edge Cases

- An unknown maintenance op string shall produce a response with `USAGE_ERROR`
  exit code and a message naming the unknown op.
- A `SkillsError` raised by the runner capability shall be caught and mapped
  to a response with the error's exit code and message.

#### Technical Specification

| Aspect       | Detail                                                                 |
| ------------ | ---------------------------------------------------------------------- |
| **Input**    | `MaintenanceRequest` (verb, skill, flags, root). Source: surface / root CLI. |
| **Output**   | `MaintenanceResponse` (ok, verb, exit_code, message, records). Destination: surface / root CLI. |
| **Protocol** | `ISkillsRunnerProtocol`                                                |
| **Method**   | `apply_automatic_transitions`, `pause`, `resume`                       |
| **Event**    | None                                                                   |
| **Error**    | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2                           |

#### Test

| Context          | When Action                   | Then Observable Result                                  |
| ---------------- | ----------------------------- | ------------------------------------------------------- |
| A `RUN` request  | `execute` with `verb=RUN`     | `MaintenanceResponse` with `ok=True`, exit code `CLEAN` |
| A `PAUSE` request | `execute` with `verb=PAUSE`  | `MaintenanceResponse` with `ok=True`, exit code `CLEAN` |
| A `RESUME` request | `execute` with `verb=RESUME` | `MaintenanceResponse` with `ok=True`, exit code `CLEAN` |

#### Metric

| Target Metric                  | Value |
| ------------------------------ | ----- |
| Transition apply p95 latency   | 5 ms  |
| Unknown-op rejection rate      | 100 % |
| Unhandled exception escape rate | 0 %  |

### FR-maintenance-003: Piner

**Description:** `SkillsMaintenanceAgent.execute(request)` shall route the
`PIN` and `UNPIN` maintenance ops to the piner capability and return a typed
`MaintenanceResponse` to the caller. The piner toggles the pinned flag via
`ISkillsPinerProtocol` and returns the resulting `PinState`.

#### Business Logic

- On `PIN`, the agent shall call `pin(skill)` and return the resulting
  `PinState` with `pinned=True`.
- On `UNPIN`, the agent shall call `unpin(skill)` and return the resulting
  `PinState` with `pinned=False`.
- A `SkillsError` raised by the piner capability shall be caught by the agent
  and mapped to a response carrying the error's exit code and message.

#### Edge Cases

- An unknown op string shall produce a response with `USAGE_ERROR` exit code
  and a message naming the unknown op.
- A `SkillsError` raised by the piner capability shall be caught and mapped
  to a response with the error's exit code and message.

#### Technical Specification

| Aspect       | Detail                                                                 |
| ------------ | ---------------------------------------------------------------------- |
| **Input**    | `MaintenanceRequest` (verb, skill, flags, root). Source: surface / root CLI. |
| **Output**   | `MaintenanceResponse` (ok, verb, exit_code, message, records). Destination: surface / root CLI. |
| **Protocol** | `ISkillsPinerProtocol`                                                 |
| **Method**   | `pin`, `unpin`                                                         |
| **Event**    | None                                                                   |
| **Error**    | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2                           |

#### Test

| Context         | When Action                  | Then Observable Result                                        |
| --------------- | ---------------------------- | ------------------------------------------------------------- |
| A `PIN` request | `execute` with `verb=PIN`    | `MaintenanceResponse` with `ok=True`, `PinState.pinned=True`   |
| An `UNPIN` request | `execute` with `verb=UNPIN` | `MaintenanceResponse` with `ok=True`, `PinState.pinned=False` |

#### Metric

| Target Metric                  | Value |
| ------------------------------ | ----- |
| Pin toggle p95 latency         | 5 ms  |
| Unknown-op rejection rate      | 100 % |
| Unhandled exception escape rate | 0 %  |

### FR-maintenance-004: Mover

**Description:** `SkillsMaintenanceAgent.execute(request)` shall route the
`MOVE` maintenance op to the mover capability and return a typed
`MaintenanceResponse` to the caller. The mover plans and applies cross-category
moves via `ISkillsMoverProtocol`.

#### Business Logic

- On `MOVE`, the agent shall call `plan_move(skill, target)` then
  `apply_move(plan)` and return the resulting `MutationOutcome`.
- The mover re-checks containment before executing the move plan.
- A `SkillsError` raised by the mover capability shall be caught by the agent
  and mapped to a response carrying the error's exit code and message.

#### Edge Cases

- An unknown op string shall produce a response with `USAGE_ERROR` exit code
  and a message naming the unknown op.
- A `SkillsError` raised by the mover capability shall be caught and mapped
  to a response with the error's exit code and message.

#### Technical Specification

| Aspect       | Detail                                                                 |
| ------------ | ---------------------------------------------------------------------- |
| **Input**    | `MaintenanceRequest` (verb, skill, flags, root). Source: surface / root CLI. |
| **Output**   | `MaintenanceResponse` (ok, verb, exit_code, message, records). Destination: surface / root CLI. |
| **Protocol** | `ISkillsMoverProtocol`                                                 |
| **Method**   | `plan_move`, `apply_move`                                              |
| **Event**    | None                                                                   |
| **Error**    | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2                           |

#### Test

| Context        | When Action                | Then Observable Result                                  |
| -------------- | -------------------------- | ------------------------------------------------------- |
| A `MOVE` request | `execute` with `verb=MOVE` | `MaintenanceResponse` with `ok=True`, exit code `CLEAN` |

#### Metric

| Target Metric                  | Value |
| ------------------------------ | ----- |
| Move plan p95 latency          | 5 ms  |
| Unknown-op rejection rate      | 100 % |
| Unhandled exception escape rate | 0 %  |

## Public Interface

| Aspect      | Detail                                                        |
| ----------- | ------------------------------------------------------------- |
| Agent       | `SkillsMaintenanceAgent`                                      |
| Aggregate   | `ISkillsMaintenanceAggregate`                                 |
| Method      | `execute`                                                     |
| Request     | `MaintenanceRequest` (verb, skill, flags, root)               |
| Response    | `MaintenanceResponse` (ok, verb, exit_code, message, records) |

## Reference

| Artifact       | Purpose                               | Link                                                |
| -------------- | ------------------------------------- | --------------------------------------------------- |
| PRD            | Business goals and scope              | [PRD.md](../../PRD.md)                              |
| Backlog        | Task tracking and implementation status | [BACKLOG.md](BACKLOG.md)                          |
| Roadmap        | Timeline, phasing, and dependencies   | [ROADMAP.md](../../ROADMAP.md)                      |
| Architecture   | System boundaries, tech stack, and infra | [ARCHITECTURE.md](../../ARCHITECTURE.md)      |