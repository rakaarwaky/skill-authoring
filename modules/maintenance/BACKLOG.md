# BACKLOG — maintenance

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-09

## Progress Overview

The maintenance module implements the `sac skills` maintenance-side verbs:
prune, purge. Each verb is owned by a capability that implements its protocol;
`SkillsMaintenanceAgent` sequences the capabilities and returns a typed
`MaintenanceResponse`.

## Backlog Status

### FR-maintenance-001: Prune

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsMaintenanceAgent.execute` routes `PRUNE` to the pruner capability via `ISkillsPrunerProtocol` |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-10                                                   |

### FR-maintenance-002: Purge

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsMaintenanceAgent.execute` routes `PURGE` to the purger capability via `ISkillsPurgerProtocol` |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-10                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| FRD          | Functional requirements                    | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
