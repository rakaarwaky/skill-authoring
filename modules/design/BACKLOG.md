# BACKLOG — design

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-10

## Progress Overview

The design module implements the `sac skills` design-side verbs:
create, adopt, lint, run, pause, resume. Each verb is owned by a
capability that implements its protocol; `SkillsDesignAgent`
sequences the capabilities and returns a typed `SkillsResult`.

## Backlog Status

### FR-DESIGN-001: Creator capability contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsCreator` implements `ISkillsCreatorProtocol` with `create_skill` and `create_category` |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-10                                                   |

### FR-DESIGN-002: Adopter capability contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsAdopter` implements `ISkillsAdopterProtocol` with `adopt` |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-10                                                   |

### FR-DESIGN-003: Linter capability contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsLinter` implements `ISkillsLinterProtocol` with `lint` |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-10                                                   |

### FR-DESIGN-004: Runner capability contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsRunner` implements `ISkillsRunnerProtocol` with `apply_automatic_transitions`, `pause`, `resume` |
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
