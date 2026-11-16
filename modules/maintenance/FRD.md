# FRD — maintenance

## Feature Overview

The maintenance feature sits in the agent layer and is called by the surface
and root CLI through the maintenance aggregate contract. It orchestrates the
prune capability — which archives idle skills and purges old archives in one
pass — and routes the `PRUNE` maintenance op to it. The agent performs no
filesystem I/O; all I/O is delegated to the capability. Archive and restore of
individual skills belong to the [storage module](../storage/FRD.md), which owns
those capabilities and its own `ISkillsArchiverProtocol` /
`ISkillsRestoreProtocol` seams.

## Functional Requirements

### FR-maintenance-001: Prune

**Description:** `SkillsMaintenanceAgent.execute(request)` shall route the
`PRUNE` maintenance op to the prune capability and return a typed
`MaintenanceResponse` to the caller. The prune capability archives idle skills
past a configurable days threshold (default 30), then purges archived skills
past a configurable archive TTL (default 60). The maintenance aggregate
contract (`ISkillsMaintenanceAggregate`) is the single entry point the surface
and root CLI use; no caller reaches the prune capability directly. The agent
performs no filesystem I/O; the prune capability owns all I/O.

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

| Aspect | Detail |
|--------|--------|
| **Input** | `MaintenanceRequest` (verb, skill, flags, root). Source: surface / root CLI. |
| **Output** | `MaintenanceResponse` (ok, verb, exit_code, message, records). Destination: surface / root CLI. |
| **Protocol** | `ISkillsPrunerProtocol` |
| **Method** | `execute` → `prune` |
| **Event** | None |
| **Error** | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2 |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| A `PRUNE` request that finds idle skills | `execute` with `verb=PRUNE` | `MaintenanceResponse` with `ok=True`, archived records populated, exit code `CLEAN` |
| A `PRUNE` request that finds old archives | `execute` with `verb=PRUNE` | `MaintenanceResponse` with `ok=True`, purged records populated, exit code `CLEAN` |
| A `PRUNE` request with `dry_run=True` | `execute` with `verb=PRUNE` and `dry_run=True` | Plan with archived/purged lists; no filesystem write occurs |
| A `PRUNE` request with `purge_days=0` | `execute` with `verb=PRUNE` and `purge_days=0` | Only the archive pass runs; no purge occurs |
| A `PRUNE` request with `days` below 1 | `execute` with `verb=PRUNE` and `days=0` | `MaintenanceResponse` with `ok=False`, exit code `1`, message naming the invalid threshold |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Dispatch p95 latency | 5 ms |
| Unknown-op rejection rate | 100 % |
| Unhandled exception escape rate | 0 % |
| Direct capability call rate from outside the agent | 0 % |