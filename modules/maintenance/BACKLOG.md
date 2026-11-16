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