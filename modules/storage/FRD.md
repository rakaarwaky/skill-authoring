# FRD — storage

## Feature Overview

The storage feature sits in the agent layer and is called by the surface and root CLI through the storage aggregate contract. It orchestrates four capabilities — archiver, backup, restore, rollback — and routes each of the four storage ops (`ARCHIVE`, `RESTORE`, `BACKUP`, `ROLLBACK`) to the matching capability. The agent performs no filesystem I/O; all I/O is delegated to the capabilities.

## Functional Requirements

### FR-storage-001: Orchestrate archive and restore operations

**Description:** `SkillsStorageAgent.execute(request)` shall route each storage op (`ARCHIVE`, `RESTORE`) to the matching capability and return a typed `StorageResponse` to the caller. The agent coordinates the capability protocols and shared kernel utilities; it performs no filesystem I/O itself.

#### Business Logic

- The agent shall delegate all filesystem I/O to the capabilities it coordinates; the agent itself holds no filesystem state.
- If a required capability was not injected at construction, the agent shall raise a root-level error at call time, not at construction.
- An op string that is not one of the four storage ops shall produce a `StorageResponse` with `USAGE_ERROR` exit code and a message naming the unknown op.
- A `SkillsError` raised by a capability shall be caught by the agent and mapped to a `StorageResponse` carrying the error's exit code and message.
- On `ARCHIVE` or `RESTORE`, an empty or absent skill name shall produce a `StorageResponse` with `ISSUES_FOUND` exit code and the message "Skill name required".

#### Edge Cases

- A missing required capability shall raise a root-level error at call time, not at agent construction.
- An unknown op string shall produce a `StorageResponse` with `USAGE_ERROR` exit code and a message naming the unknown op.
- A `SkillsError` raised by any capability shall be caught and mapped to a `StorageResponse` with the error's exit code and message.
- On `ARCHIVE` or `RESTORE`, an `OSError` from the capability shall be caught and returned as a `StorageResponse` with `ISSUES_FOUND` exit code.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | `StorageRequest` (verb, query, root, flags). Source: surface / root CLI. |
| **Output** | `StorageResponse` (ok, verb, exit_code, message, root). Destination: surface / root CLI. |
| **Protocol** | `ISkillsStorageAggregate` |
| **Method** | `execute` |
| **Event** | None |
| **Error** | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2 |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| An `ARCHIVE` request | The surface invokes `execute` with `verb=ARCHIVE` | `StorageResponse` with `ok=True`, exit code `CLEAN` |
| A `RESTORE` request | The surface invokes `execute` with `verb=RESTORE` | `StorageResponse` with `ok=True`, exit code `CLEAN` |
| An unknown op string | The surface invokes `execute` with an op string outside the storage set | `StorageResponse` with `ok=False`, exit code `USAGE_ERROR`, message naming the unknown op |
| An `ARCHIVE` request missing the skill name | The surface invokes `execute` with `verb=ARCHIVE` and empty query | `StorageResponse` with `ok=False`, exit code `ISSUES_FOUND`, message "Skill name required" |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Dispatch p95 latency | 5 ms |
| Unknown-op rejection rate | 100 % |
| Unhandled exception escape rate | 0 % |

### FR-storage-002: Backup snapshot creation and pruning

**Description:** `SkillsBackup.create_snapshot(root)` shall create a content-addressed snapshot of the pack under `.lifecycle_backups/` and prune old snapshots beyond the configured keep count.

#### Business Logic

- The snapshot shall be written to `.lifecycle_backups/<timestamp>/` containing a gzipped tarball and a manifest file.
- Every file in the pack shall be hashed (sha256) and recorded in the manifest with path, sha256, and size.
- Pruning shall remove the oldest snapshots beyond `backup_keep`, respecting any excluded snapshot names.

#### Edge Cases

- A missing pack root shall raise `SkillsRootError`.
- A tarball extraction path that escapes the target directory shall fail closed.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | `root` (`Path`). Source: agent. |
| **Output** | Snapshot directory `Path`. Destination: `.lifecycle_backups/`. |
| **Protocol** | `ISkillsBackupProtocol` |
| **Method** | `create_snapshot`, `prune_old_snapshots` |
| **Event** | None |
| **Error** | `OSError`, `SkillsRootError` |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| A valid root | `create_snapshot(root)` | Snapshot directory created under `.lifecycle_backups/` |
| A root with more snapshots than `backup_keep` | `prune_old_snapshots(root)` | Oldest snapshots removed, keep count retained |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Snapshot creation failure rate | 0 % |
| Pruned-snapshot accuracy | 100 % |

### FR-storage-003: Rollback snapshot restoration

**Description:** `SkillsRollback.rollback(root, id_)` shall restore the pack tree from a stored snapshot, staging the live tree so the operation is reversible.

#### Business Logic

- The snapshot identified by `id_` (or the latest if `id_` is None) shall be extracted over the live tree.
- The current live tree shall be moved to a staging directory before extraction so it can be recovered on failure.
- A snapshot id containing path separators or `..` shall be rejected.

#### Edge Cases

- No snapshots available shall raise `SkillsUsageError`.
- An invalid or escaping snapshot id shall raise `SkillsUsageError`.
- A failed extraction shall restore the staged tree and raise `MutationConflictError`.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | `root` (`Path`), `id_` (str or None). Source: agent / CLI flags. |
| **Output** | `dict` with `snapshot`, `staging`, `restored`. |
| **Protocol** | `ISkillsRollbackProtocol` |
| **Method** | `rollback` |
| **Event** | None |
| **Error** | `OSError`, `SkillsUsageError`, `MutationConflictError` |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| No snapshots exist | `rollback(root)` | `SkillsUsageError` raised |
| A valid snapshot id | `rollback(root, id_)` | Pack tree restored; `restored=True` returned |
| An escaping snapshot id | `rollback(root, "../evil")` | `SkillsUsageError` raised |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Rollback success rate | 100 % |
| Failed-rollback tree recovery rate | 100 % |

### FR-storage-004: Storage agent wiring and contract

**Description:** The storage aggregate contract shall define a single `execute(StorageRequest) → StorageResponse` entry point that the agent implements. The root composition root shall wire the agent into the composed facade so that the surface and CLI can call the storage ops through one stable interface.

#### Business Logic

- The aggregate contract shall be an abstract base class with one abstract method: `execute`.
- The agent shall implement the aggregate contract; the root composition root shall instantiate the agent and register it in the composed facade.
- The aggregate contract shall live in the shared storage contract module, not in the feature's source tree.
- The surface and root CLI shall call storage ops exclusively through the aggregate contract; no direct capability calls from outside the agent.

#### Edge Cases

- A composition root that wires the agent without a required capability shall raise a root-level error at the point that op is first called, not at construction.
- A surface that calls a storage op through the aggregate contract with an invalid op string shall receive a `StorageResponse` with `USAGE_ERROR`.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | `StorageRequest`. Source: surface / root CLI. |
| **Output** | `StorageResponse`. Destination: surface / root CLI. |
| **Protocol** | `ISkillsStorageAggregate` |
| **Method** | `execute` |
| **Event** | None |
| **Error** | `USAGE_ERROR` 2, `ISSUES_FOUND` 1 |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| The agent is constructed and registered in the root composition root | The surface calls a storage op through the facade | The agent's `execute` is invoked; a `StorageResponse` is returned |
| The agent is constructed without the archiver capability and `ARCHIVE` is called | `execute(StorageRequest(verb=ARCHIVE))` | A root-level error is raised naming the missing capability |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Direct capability call rate from outside the agent | 0 % |
| Aggregate contract test pass rate | 100 % |

## Public Interface

| Aspect     | Detail                         |
|------------|--------------------------------|
| Agent      | `SkillsStorageAgent`           |
| Aggregate  | `ISkillsStorageAggregate`      |
| Method     | `execute`                      |
| Request    | `StorageRequest` (verb, query, root, flags) |
| Response   | `StorageResponse` (ok, verb, exit_code, message, root) |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| Backlog      | Task tracking and implementation status    | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
