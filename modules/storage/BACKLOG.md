# BACKLOG — storage

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-09

## Progress Overview

The storage module implements the storage-side verbs: archive, restore,
backup, rollback. Each verb is owned by a capability that implements its
protocol; `SkillsStorageAgent` sequences the capabilities and returns a
typed `StorageResponse`.

## Backlog Status

### FR-storage-001: Orchestrate archive and restore operations

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsArchiver` and `SkillsRestore` implement their protocols; `SkillsStorageAgent` routes ARCHIVE and RESTORE |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-storage-002: Backup snapshot creation and pruning

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsBackup` implements create_snapshot and prune_old_snapshots |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-storage-003: Rollback snapshot restoration

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsRollback` restores the pack tree from a stored snapshot |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-storage-004: Storage agent wiring and contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `ISkillsStorageAggregate` in `shared/src/storage/`; agent registered in root |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| FRD          | Functional requirements                    | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
