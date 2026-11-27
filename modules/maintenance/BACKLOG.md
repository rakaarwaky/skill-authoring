# BACKLOG — maintenance

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-16

## Progress Overview

The maintenance module implements the `sac` maintenance-side verb: prune. The
prune capability owns two passes — archive idle skills, then purge old
archives — and implements `ISkillsPrunerProtocol`.
`SkillsMaintenanceAgent` sequences the capability and returns a typed
`MaintenanceResponse`.

## Backlog Status

### FR-maintenance-001: Prune

| Aspect      | Detail                                                 |
| ----------- | ------------------------------------------------------ |
| State       | Done                                                   |
| Done        | `SkillsMaintenanceAgent.execute` routes `PRUNE` to the |
|             | prune capability via `ISkillsPrunerProtocol`; the      |
|             | capability archives idle skills (>=30d) and purges     |
|             | old archives (>=60d) in one command                  |
| In Progress | None                                                   |
| Risk        | None                                                   |
| Updated     | 2026-11-16                                             |

### FR-maintenance-002: Runner

| Aspect      | Detail                                                 |
| ----------- | ------------------------------------------------------ |
| State       | Removed (2026-11-27)                                   |
| Done        | Runner capability and its `RUN`, `PAUSE`, and `RESUME` |
|             | verbs removed; no longer available                     |
| In Progress | None                                                   |
| Risk        | None                                                   |
| Updated     | 2026-11-27                                             |

### FR-maintenance-003: Piner

| Aspect      | Detail                                                 |
| ----------- | ------------------------------------------------------ |
| State       | Done                                                   |
| Done        | `SkillsMaintenanceAgent.execute` routes `PIN` and      |
|             | `UNPIN` to the piner capability via `ISkillsPinerProtocol`; |
|             | the resulting `PinState` is returned to the caller     |
| In Progress | None                                                   |
| Risk        | None                                                   |
| Updated     | 2026-11-16                                             |

### FR-maintenance-004: Mover

| Aspect      | Detail                                                 |
| ----------- | ------------------------------------------------------ |
| State       | Done                                                   |
| Done        | `SkillsMaintenanceAgent.execute` routes `MOVE` to the  |
|             | mover capability via `ISkillsMoverProtocol`;           |
|             | `plan_move` then `apply_move` executes the move plan   |
| In Progress | None                                                   |
| Risk        | None                                                   |
| Updated     | 2026-11-16                                             |

### FR-maintenance-005: Usage lifecycle + session scan

| Aspect      | Detail                                                 |
| ----------- | ------------------------------------------------------ |
| State       | Done                                                   |
| Done        | `SkillsMaintenanceAgent.execute` routes `USAGE` and    |
|             | `STATUS` to the usage capability via                   |
|             | `ISkillsUsageProtocol`; `scan_sessions`, `write_usage`, |
|             | `fold_used_count_into_usage`, and `curated_report`     |
|             | are implemented in `capabilties_skills_usage.py`.       |
|             | Phrases/memory mining dropped with observability module |
| In Progress | None                                                   |
| Risk        | None                                                   |
| Updated     | 2026-11-27                                             |

## Reference

| Artifact     | Purpose                                           |
| ------------ | ------------------------------------------------- |
| PRD          | Business goals and scope                          |
|              | [PRD.md](../../../../../PRD.md)                   |
| FRD          | Functional requirements                           |
|              | [FRD.md](FRD.md)                                  |
| Roadmap      | Timeline, phasing, and dependencies               |
|              | [ROADMAP.md](../../../../../ROADMAP.md)           |
| Architecture | System boundaries, tech stack, and infra          |
|              | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |