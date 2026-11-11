# FRD — maintenance

## Feature Overview

The maintenance feature sits in the agent layer and is called by the surface
and root CLI through the maintenance aggregate contract. It orchestrates two
capabilities — prune and purge — and routes each of the maintenance ops
(`PRUNE`, `PURGE`) to the matching capability. The agent performs no filesystem
I/O; all I/O is delegated to the capabilities. Archive and restore of
individual skills belong to the [storage module](../storage/FRD.md), which owns
those capabilities and its own `ISkillsArchiverProtocol` /
`ISkillsRestoreProtocol` seams.

## Functional Requirements

### FR-maintenance-001: Prune

**Description:** `SkillsMaintenanceAgent.execute(request)` shall route the
`PRUNE` maintenance op to the prune capability and return a typed
`MaintenanceResponse` to the caller. The maintenance aggregate contract
(`ISkillsMaintenanceAggregate`) is the single entry point the surface and root
CLI use; no caller reaches the prune capability directly. The agent performs no
filesystem I/O; the prune capability owns all I/O.

#### Business Logic — Prune

- On `PRUNE`, the agent shall require a `--days` threshold flag; a missing
  threshold shall produce a `USAGE_ERROR` result.
- On `PRUNE` with `dry_run=True`, the agent shall return a plan without
  archiving any skills.
- An op string that is not one of the maintenance ops shall produce a response
  with `USAGE_ERROR` exit code and a message naming the unknown op.
- A `SkillsError` raised by the prune capability shall be caught by the agent
  and mapped to a response carrying the error's exit code and message.
- A missing prune capability at construction shall raise a root-level error at
  the first `PRUNE` call, not at construction.

#### Edge Cases — Prune

- A `PRUNE` request with no `days` in its flags shall produce a
  `MaintenanceResponse` with `ok=False`, exit code `USAGE_ERROR`, and a message
  naming the missing flag.
- An unknown op string shall produce a response with `USAGE_ERROR` exit code
  and a message naming the unknown op.
- A `SkillsError` raised by the prune capability shall be caught and mapped to
  a response with the error's exit code and message.

#### Technical Specification — Prune

| Aspect       | Detail                                                     |
| ------------ | ---------------------------------------------------------- |
| **Input**    | `MaintenanceRequest` (verb, skill, flags, root). Source:   |
|              | surface / root CLI.                                        |
| **Output**   | `MaintenanceResponse` (ok, verb, exit_code, message, op-   |
|              | specific payload fields). Destination: surface / root CLI. |
| **Protocol** | `ISkillsPrunerProtocol`                                    |
| **Method**   | `execute` → `prune`                                        |
| **Event**    | None                                                       |
| **Error**    | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2               |

#### Test — Prune

| When Action                                   | Then Observable Result       |
| --------------------------------------------- | ---------------------------- |
| A `PRUNE` request that finds idle skills —    | `MaintenanceResponse` with   |
| `execute` with `verb=PRUNE`                   | `ok=True`, `pruned`          |
|                                               | populated, exit code `CLEAN` |
| A `PRUNE` request that finds no idle skills — | `MaintenanceResponse` with   |
| `execute` with `verb=PRUNE`                   | `ok=True`, `kept` populated, |
|                                               | exit code `CLEAN`            |
| A `PRUNE` request with `dry_run=True` —       | Plan with `pruned` list; no  |
| `execute` with `verb=PRUNE` and               | filesystem write occurs      |
| `dry_run=True`                                |                              |
| A `PRUNE` request missing days — `execute`    | `MaintenanceResponse` with   |
| with `verb=PRUNE` and no days in flags        | `ok=False`, exit code        |
|                                               | `USAGE_ERROR`, message       |
|                                               | naming the missing flag      |

#### Metric — Prune

| Target Metric                                      | Value |
| -------------------------------------------------- | ----- |
| Dispatch p95 latency                               | 5 ms  |
| Unknown-op rejection rate                          | 100 % |
| Unhandled exception escape rate                    | 0 %   |
| Direct capability call rate from outside the agent | 0 %   |

### FR-maintenance-002: Purge

**Description:** `SkillsMaintenanceAgent.execute(request)` shall route the
`PURGE` maintenance op to the purge capability and return a typed
`MaintenanceResponse` to the caller. The maintenance aggregate contract
(`ISkillsMaintenanceAggregate`) is the single entry point the surface and root
CLI use; no caller reaches the purge capability directly. The agent performs no
filesystem I/O; the purge capability owns all I/O.

#### Business Logic — Purge

- On `PURGE`, the agent shall delete archived skills past TTL, or a single
  named archived skill.
- An empty or absent skill name on `PURGE` with `apply=True` shall produce a
  `MaintenanceResponse` with `ISSUES_FOUND` exit code and the message "Skill
  name required".
- An op string that is not one of the maintenance ops shall produce a response
  with `USAGE_ERROR` exit code and a message naming the unknown op.
- A `SkillsError` raised by the purge capability shall be caught by the agent
  and mapped to a response carrying the error's exit code and message.
- A missing purge capability at construction shall raise a root-level error at
  the first `PURGE` call, not at construction.

#### Edge Cases — Purge

- An empty or absent skill name on `PURGE` shall produce a response with
  `ISSUES_FOUND` exit code and the message "Skill name required".
- An unknown op string shall produce a response with `USAGE_ERROR` exit code
  and a message naming the unknown op.
- A `SkillsError` raised by the purge capability shall be caught and mapped to
  a response with the error's exit code and message.

#### Technical Specification — Purge

| Aspect       | Detail                                                     |
| ------------ | ---------------------------------------------------------- |
| **Input**    | `MaintenanceRequest` (verb, skill, flags, root). Source:   |
|              | surface / root CLI.                                        |
| **Output**   | `MaintenanceResponse` (ok, verb, exit_code, message, op-   |
|              | specific payload fields). Destination: surface / root CLI. |
| **Protocol** | `ISkillsPurgerProtocol`                                    |
| **Method**   | `execute` → `purge`                                        |
| **Event**    | None                                                       |
| **Error**    | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2               |

#### Test — Purge

| When Action                                   | Then Observable Result       |
| --------------------------------------------- | ---------------------------- |
| A `PURGE` request with `apply=True` —         | `MaintenanceResponse` with   |
| `execute` with `verb=PURGE`                   | `ok=True`, `purged`          |
|                                               | populated                    |
| A valid `PURGE` request — `execute` with      | `MaintenanceResponse` with   |
| `verb=PURGE`                                  | `ok=True`, message populated |
| A `PURGE` request with a missing skill name — | `MaintenanceResponse` with   |
| `execute` with `verb=PURGE` and an empty      | `ok=False`, exit code        |
| query                                         | `ISSUES_FOUND`, message      |
|                                               | "Skill name required"        |
| A purge capability is called with a valid     | Result dict with `purged`    |
| root — `purge` returns a result dict          | and `kept` lists             |

#### Metric — Purge

| Target Metric                                      | Value |
| -------------------------------------------------- | ----- |
| Dispatch p95 latency                               | 5 ms  |
| Unknown-op rejection rate                          | 100 % |
| Unhandled exception escape rate                    | 0 %   |
| Direct capability call rate from outside the agent | 0 %   |

## Public Interface

| Aspect    | Detail                                                           |
| --------- | ---------------------------------------------------------------- |
| Agent     | `SkillsMaintenanceAgent`                                         |
| Aggregate | `ISkillsMaintenanceAggregate`                                    |
| Method    | `execute`                                                        |
| Request   | `MaintenanceRequest` (verb, skill, flags, root)                  |
| Response  | `MaintenanceResponse` (ok, verb, exit_code, message, op-specific |
|           | fields)                                                          |

## Reference

| Artifact     | Purpose                                           |
| ------------ | ------------------------------------------------- |
| PRD          | Business goals and scope                          |
|              | [PRD.md](../../../../../PRD.md)                   |
| Backlog      | Task tracking and implementation status           |
|              | [BACKLOG.md](BACKLOG.md)                          |
| Roadmap      | Timeline, phasing, and dependencies               |
|              | [ROADMAP.md](../../../../../ROADMAP.md)           |
| Architecture | System boundaries, tech stack, and infra          |
|              | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
