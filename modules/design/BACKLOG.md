# BACKLOG — design

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-17

## Progress Overview

The design module implements the `sac skills` design-side verbs: create and
lint. Each verb is owned by a capability that implements its protocol;
`SkillsDesignAgent` sequences the capabilities and returns a typed
`SkillsResult`. Lifecycle verbs (`run`, `pause`, `resume`) belong to the
maintenance module via `ISkillsRunnerProtocol` and are tracked in
[maintenance/BACKLOG.md](../maintenance/BACKLOG.md).

## Backlog Status

### FR-DESIGN-001: Creator capability contract

| Aspect        | Detail                                                       |
| ------------- | ------------------------------------------------------------ |
| State         | Done                                                         |
| Done          | `SkillsCreator` implements `ISkillsCreatorProtocol` with     |
|               | `create_skill` and `create_category`                         |
| In Progress   | None                                                         |
| Risk          | None                                                         |
| Updated       | 2026-11-17                                                   |

### FR-DESIGN-002: Linter capability contract

| Aspect        | Detail                                                       |
| ------------- | ------------------------------------------------------------ |
| State         | Done                                                         |
| Done          | `SkillsLinter` implements `ISkillsLinterProtocol` with       |
|               | `lint`                                                       |
| In Progress   | None                                                         |
| Risk          | None                                                         |
| Updated       | 2026-11-17                                                   |

## Reference

| Artifact       | Purpose                      | Link                         |
| -------------- | ---------------------------- | ---------------------------- |
| PRD            | Business goals and scope     | [PRD.md](../../../../../PRD.md) |
| FRD            | Functional requirements      | [FRD.md](FRD.md)             |
| Roadmap        | Timeline, phasing, and       | [ROADMAP.md](../../../../../ROADMAP.md) |
|                | dependencies                 |                              |
| Architecture   | System boundaries, tech      | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
|                | stack, and infra             |                              |