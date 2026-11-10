# FRD — storage

## Feature Overview

The storage feature sits in the agent layer and is called by the surface and root CLI through the storage aggregate contract. It orchestrates five capabilities — archiver, backup, bootstrap, restore, rollback — and routes each storage op to the matching capability. The agent performs no filesystem I/O; all I/O is delegated to the capabilities.

## Functional Requirements

### FR-storage-001: Archive a live skill

**Description:**
The feature shall move a live skill from its category directory into the archive directory under `_archive/`, resolving the skill's source directory and placing it at `_archive/<category>/<skill>/`. No filesystem state is held by the agent; the archiver capability performs the move.

#### Business Logic

- The archiver shall resolve the skill's source directory under the pack root.
- The archive destination shall be `_archive/<category>/<skill>/`.
- The archiver shall reject an archive whose destination already exists.
- Every computed destination shall be asserted to remain inside the pack root before any write, and re-checked at apply time.

#### Edge Cases

- An archive destination that already exists shall produce a conflict error and overwrite nothing.
- A computed destination that escapes the pack root shall fail closed before writing.

#### Technical Specification

| Aspect | Detail |
| -------- | -------- |
| **Input** | `skill` (skill name), `root` (pack root). Source: agent / caller. |
| **Output** | Archive destination path. Destination: `_archive/` under the pack root. |
| **Protocol** | `ISkillsArchiverProtocol` |
| **Method** | `plan_archive`, `apply_archive` |
| **Event** | None |
| **Error** | `MutationConflictError`, `SkillsUsageError` |

#### Test

| Context | When Action | Then Observable Result |
| --------- | ------------- | ------------------------ |
| A live skill exists | The caller invokes archive | The skill is moved under `_archive/<category>/<skill>/` |
| An archive destination already exists | The caller invokes archive | A conflict error is raised and nothing is overwritten |
| A computed destination escapes the pack root | The caller invokes archive | The operation fails closed with a containment error |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Archive containment violation rate | 0 % |

### FR-storage-002: Create a backup snapshot

**Description:**
The feature shall create a content-addressed snapshot of the pack under `.lifecycle_backups/<timestamp>/`, containing a gzipped tarball and a manifest file, and prune old snapshots beyond the configured keep count.

#### Business Logic

- The snapshot shall be written under `.lifecycle_backups/<timestamp>/`.
- The snapshot shall contain a gzipped tarball and a manifest file.
- Every file in the pack shall be hashed (sha256) and recorded in the manifest with path, sha256, and size.
- Pruning shall remove the oldest snapshots beyond the configured keep count, respecting any excluded snapshot names.

#### Edge Cases

- A missing pack root shall raise `SkillsRootError`.
- A tarball extraction path that escapes the target directory shall fail closed.

#### Technical Specification

| Aspect | Detail |
| -------- | -------- |
| **Input** | `root` (pack root). Source: agent / caller. |
| **Output** | Snapshot directory path. Destination: `.lifecycle_backups/`. |
| **Protocol** | `ISkillsBackupProtocol` |
| **Method** | `create_snapshot`, `prune_old_snapshots` |
| **Event** | None |
| **Error** | `OSError`, `SkillsRootError` |

#### Test

| Context | When Action | Then Observable Result |
| --------- | ------------- | ------------------------ |
| A valid pack root | The caller invokes create_snapshot | A snapshot directory is created under `.lifecycle_backups/` containing a tarball and a manifest |
| More snapshots exist than the keep count | The caller invokes prune_old_snapshots | The oldest snapshots are removed and the keep count is retained |
| A missing pack root | The caller invokes create_snapshot | `SkillsRootError` is raised |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Snapshot creation failure rate | 0 % |

### FR-storage-003: Bootstrap a skill pack root

**Description:**
The feature shall initialize a skill pack root by creating the standard category directories and writing the pack sidecar used by every verb.

#### Business Logic

- Bootstrap shall create the standard category directories under the pack root.
- Bootstrap shall write the pack sidecar used by every verb.
- Bootstrap shall not fail when the root already exists.

#### Edge Cases

- A missing root shall be created if possible.
- Existing category directories shall be left in place.
- No root given shall use the default pack root.

#### Technical Specification

| Aspect | Detail |
| -------- | -------- |
| **Input** | `root` (pack root or None for default). Source: agent / caller. |
| **Output** | `StorageResponse` whose manifest holds the resolved pack root and the list of created category directories. Destination: caller. |
| **Protocol** | `ISkillsBootstrapProtocol` |
| **Method** | `bootstrap` |
| **Event** | None |
| **Error** | `OSError` |

#### Test

| Context | When Action | Then Observable Result |
| --------- | ------------- | ------------------------ |
| No pack root exists | The caller invokes bootstrap | Standard category directories and the pack sidecar are created |
| A pack root already exists | The caller invokes bootstrap | Existing directories are left in place; the response reports no new creations |
| No root is given | The caller invokes bootstrap | The default pack root is used |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Bootstrap idempotency rate | 100 % |

### FR-storage-004: Restore an archived skill

**Description:**
The feature shall move an archived skill from `_archive/<category>/<skill>/` back to its live category directory, re-anchoring the skill after the move.

#### Business Logic

- Restore shall move an archived skill from `_archive/<category>/<skill>/` back to its live category directory.
- Restore shall re-anchor the skill after moving it.

#### Edge Cases

- A skill that is not archived shall produce a not-found error.
- A restore destination that already exists shall produce a conflict error and overwrite nothing.

#### Technical Specification

| Aspect | Detail |
| -------- | -------- |
| **Input** | `skill` (skill name), `root` (pack root or None). Source: agent / caller. |
| **Output** | Restore result. Destination: live pack under the category directory. |
| **Protocol** | `ISkillsRestoreProtocol` |
| **Method** | `restore` |
| **Event** | None |
| **Error** | `SkillNotFoundError`, `MutationConflictError` |

#### Test

| Context | When Action | Then Observable Result |
| --------- | ------------- | ------------------------ |
| An archived skill exists | The caller invokes restore | The skill is restored to its live category directory |
| A skill is not archived | The caller invokes restore | A not-found error is raised |
| A restore destination already exists | The caller invokes restore | A conflict error is raised and nothing is overwritten |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Restore success rate | 100 % |

### FR-storage-005: Rollback the pack tree

**Description:**
The feature shall restore the pack tree from a stored snapshot, staging the live tree before extraction so the operation is reversible.

#### Business Logic

- Rollback shall extract the snapshot identified by id (or the latest if id is None) over the live tree.
- Rollback shall move the current live tree to a staging directory before extraction so it can be recovered on failure.
- Rollback shall reject a snapshot id containing path separators or `..`.

#### Edge Cases

- No snapshots available shall raise `SkillsUsageError`.
- An invalid or escaping snapshot id shall raise `SkillsUsageError`.
- A failed extraction shall restore the staged tree and raise `MutationConflictError`.

#### Technical Specification

| Aspect | Detail |
| -------- | -------- |
| **Input** | `root` (pack root), `id_` (snapshot id or None). Source: agent / caller. |
| **Output** | dict with `snapshot`, `staging`, `restored`. Destination: live pack tree. |
| **Protocol** | `ISkillsRollbackProtocol` |
| **Method** | `rollback` |
| **Event** | None |
| **Error** | `OSError`, `SkillsUsageError`, `MutationConflictError` |

#### Test

| Context | When Action | Then Observable Result |
| --------- | ------------- | ------------------------ |
| No snapshots exist | The caller invokes rollback | `SkillsUsageError` is raised |
| A valid snapshot id | The caller invokes rollback(id_) | The pack tree is restored and `restored=True` is returned |
| An escaping snapshot id | The caller invokes rollback("../evil") | `SkillsUsageError` is raised |
| A failed extraction | The caller invokes rollback | The staged tree is restored and `MutationConflictError` is raised |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Rollback success rate | 100 % |
| Failed-rollback tree recovery rate | 100 % |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | `SkillsStorageAgent` |
| Aggregate  | `ISkillsStorageAggregate` |
| Method     | `execute` |
| Request    | `StorageRequest` |
| Response   | `StorageResponse` |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| Backlog      | Task tracking and implementation status    | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
