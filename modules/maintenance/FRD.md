# FRD — maintenance

## Feature Overview

The maintenance feature sits in the agent layer and is called by the surface and root CLI through the maintenance aggregate contract. It orchestrates two capabilities — prune and purge — plus an optional archiver/restorer, and routes each of the maintenance ops (`PRUNE`, `PURGE`) to the matching capability. The agent performs no filesystem I/O; all I/O is delegated to the capabilities.

## Functional Requirements

### FR-maintenance-001: Orchestrate maintenance-side skill operations

**Description:** `SkillsMaintenanceAgent.execute(request)` shall route each maintenance op (`PRUNE`, `PURGE`) to the matching capability and return a typed `MaintenanceResponse` to the caller. The agent coordinates the capability protocols and shared kernel utilities; it performs no filesystem I/O itself.

#### Business Logic

- The agent shall delegate all filesystem I/O to the capabilities it coordinates; the agent itself holds no filesystem state.
- If a required capability was not injected at construction, the agent shall raise a root-level error at call time, not at construction.
- An op string that is not one of the maintenance ops shall produce a response with `USAGE_ERROR` exit code and a message naming the unknown op.
- A `SkillsError` raised by a capability shall be caught by the agent and mapped to a response carrying the error's exit code and message.
- On `PRUNE`, the agent shall require a `--days` flag; a missing threshold shall produce a `USAGE_ERROR` result.
- On `PRUNE` with `dry_run=True`, the agent shall return a plan without archiving any skills.
- On `PURGE`, the agent shall delete archived skills past TTL or a single named archived skill.

#### Edge Cases

- A missing required capability shall raise a root-level error at call time, not at agent construction.
- An empty or absent skill name on `PURGE` shall produce a response with `ISSUES_FOUND` exit code and the message "Skill name required".
- An unknown op string shall produce a response with `USAGE_ERROR` exit code and a message naming the unknown op.
- A `SkillsError` raised by any capability shall be caught and mapped to a response with the error's exit code and message.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | `MaintenanceRequest` (verb, skill, flags, root). Source: surface / root CLI. |
| **Output** | `MaintenanceResponse` (ok, verb, exit_code, message, op-specific payload fields). Destination: surface / root CLI. |
| **Protocol** | `ISkillsMaintenanceAggregate` |
| **Method** | `execute` |
| **Event** | None |
| **Error** | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2 |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| A `PRUNE` request that finds idle skills | The surface invokes `execute` with `verb=PRUNE` | `MaintenanceResponse` with `ok=True`, `pruned` populated, exit code `CLEAN` |
| A `PRUNE` request that finds no idle skills | The surface invokes `execute` with `verb=PRUNE` | `MaintenanceResponse` with `ok=True`, `kept` populated, exit code `CLEAN` |
| A `PURGE` request with `apply=True` | The surface invokes `execute` with `verb=PURGE` | `MaintenanceResponse` with `ok=True`, `purged` populated |
| A `PRUNE` request missing days | The surface invokes `execute` with `verb=PRUNE` and no days in flags | `MaintenanceResponse` with `ok=False`, exit code `USAGE_ERROR`, message naming the missing flag |
| A valid `PURGE` request | The surface invokes `execute` with `verb=PURGE` | `MaintenanceResponse` with `ok=True`, message populated |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Dispatch p95 latency | 5 ms |
| Unknown-op rejection rate | 100 % |
| Unhandled exception escape rate | 0 % |

### FR-maintenance-002: Capability contract implementation

**Description:** Each of the two capability modules shall implement its corresponding protocol. No capability shall import a sibling capability; cross-capability data shall flow through shared kernel protocols or shared kernel utilities.

#### Business Logic

- The prune capability shall implement the pruner protocol: `prune`.
- The purge capability shall implement the purger protocol: `purge`.
- No capability module shall import another capability module directly; data crossing capability boundaries shall go through shared kernel protocols or shared kernel utilities.

#### Edge Cases

- A capability module that imports a sibling capability module shall be flagged by the architecture scanner.
- A missing skill name on `purge` shall raise an error that the agent maps to a `MaintenanceResponse` with `ISSUES_FOUND`.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | Capability-specific arguments as defined by each protocol. Source: agent. |
| **Output** | Capability-specific results as defined by each protocol. Destination: agent. |
| **Protocol** | Pruner protocol, Purger protocol |
| **Method** | `prune`, `purge` |
| **Event** | None |
| **Error** | `OSError`, `SkillsError` subclasses; agent maps them to response exit codes |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| A prune capability is constructed and `prune` is called with `dry_run=True` | Prune plan is returned | Plan with `pruned` list; no filesystem write occurs |
| A purge capability is called with a valid root | `purge` returns a result dict | Result dict with `purged` and `kept` lists |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Sibling-capability import count | 0 |
| Capability contract test pass rate | 100 % |

### FR-maintenance-003: Maintenance aggregate contract

**Description:** The maintenance aggregate contract shall define a single `execute(MaintenanceRequest) → MaintenanceResponse` entry point that the agent implements. The root composition root shall wire the agent into the composed facade so that the surface and CLI can call the maintenance ops through one stable interface.

#### Business Logic

- The aggregate contract shall be an abstract base class with one abstract method: `execute`.
- The agent shall implement the aggregate contract; the root composition root shall instantiate the agent and register it in the composed facade.
- The aggregate contract shall live in the shared maintenance contract module, not in the feature's source tree.
- The surface and root CLI shall call maintenance ops exclusively through the aggregate contract; no direct capability calls from outside the agent.

#### Edge Cases

- A composition root that wires the agent without the prune capability shall raise a root-level error at the point `PRUNE` is first called, not at construction.
- A surface that calls a maintenance op through the aggregate contract with an invalid verb string shall receive a `MaintenanceResponse` with `USAGE_ERROR`.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | `MaintenanceRequest`. Source: surface / root CLI. |
| **Output** | `MaintenanceResponse`. Destination: surface / root CLI. |
| **Protocol** | `ISkillsMaintenanceAggregate` |
| **Method** | `execute` |
| **Event** | None |
| **Error** | `USAGE_ERROR` 2, `ISSUES_FOUND` 1 |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| The agent is constructed and registered in the root composition root | The surface calls a maintenance op through the facade | The agent's `execute` is invoked; a `MaintenanceResponse` is returned |
| The agent is constructed without the prune capability and `PRUNE` is called | `execute(MaintenanceRequest(verb=PRUNE))` | A root-level error is raised naming the missing capability |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Direct capability call rate from outside the agent | 0 % |
| Aggregate contract test pass rate | 100 % |

## Public Interface

| Aspect     | Detail                         |
|------------|--------------------------------|
| Agent      | `SkillsMaintenanceAgent`       |
| Aggregate  | `ISkillsMaintenanceAggregate`  |
| Method     | `execute`                      |
| Request    | `MaintenanceRequest` (verb, skill, flags, root) |
| Response   | `MaintenanceResponse` (ok, verb, exit_code, message, op-specific fields) |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| Backlog      | Task tracking and implementation status    | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
