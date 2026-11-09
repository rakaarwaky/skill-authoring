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

### FR-maintenance-001: Orchestrate maintenance-side skill operations

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsMaintenanceAgent.execute` routes prune/purge ops via `ISkillsMaintenanceAggregate` |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-maintenance-002: Capability contract implementation

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Two capability files implement their protocols; no sibling imports |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-maintenance-003: Maintenance aggregate contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `ISkillsMaintenanceAggregate` in `shared/src/maintenance/`; agent registered in root |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-maintenance-004: Maintenance archive/restore contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `ISkillsArchiverProtocol` and `ISkillsRestorerProtocol` in `shared/src/maintenance/`; aggregate declares archive/restore |
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
