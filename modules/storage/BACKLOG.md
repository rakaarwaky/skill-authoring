# BACKLOG — storage

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-16

## Progress Overview

The storage module implements the storage-side verbs: archive, restore,
export. Each verb is owned by a capability that implements its protocol;
`SkillsStorageAgent` sequences the capabilities and returns a typed
`StorageResponse`.

## Backlog Status

### FR-storage-001: Orchestrate archive and restore operations

| Aspect      | Detail      |
| ----------- | ----------- |
| State       | Done        |
| Done        | Wired       |
| In Progress | None        |
| Risk        | None        |
| Updated     | 2026-11-09  |

`SkillsArchiver` and `SkillsRestore` implement their protocols;
`SkillsStorageAgent` routes ARCHIVE and RESTORE.

### FR-storage-002: Storage agent wiring and contract

| Aspect      | Detail      |
| ----------- | ----------- |
| State       | Done        |
| Done        | Wired       |
| In Progress | None        |
| Risk        | None        |
| Updated     | 2026-11-09  |

`ISkillsStorageAggregate` in `shared/src/storage/`; agent registered in
root.

### FR-storage-003: Export a skill pack to a single Markdown document

| Aspect      | Detail      |
| ----------- | ----------- |
| State       | Done        |
| Done        | Wired       |
| In Progress | None        |
| Risk        | None        |
| Updated     | 2026-11-16  |

`SkillsExporter` implements export; skill folder is concatenated into a
single Markdown file at `.export/<namaskill>.md`.

## Reference

| Artifact     | Purpose                                  |
| ------------ | ---------------------------------------- |
| PRD          | Business goals and scope                 |
| FRD          | Functional requirements                  |
| Roadmap      | Timeline, phasing, and dependencies      |
| Architecture | System boundaries, tech stack, and infra |

Links: [PRD.md](../../../../../PRD.md), [FRD.md](FRD.md),
[ROADMAP.md](../../../../../ROADMAP.md),
[ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
