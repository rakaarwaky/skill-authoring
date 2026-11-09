# BACKLOG — mcp

FRD: none
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-04

## Progress Overview

The skills MCP adapter surface ships `surface_mcp_command.py` exposing every
`24` design-side `sac` skill verbs as MCP tools (1:1 CLI equivalence).
Each tool delegates to the composed `ISkillsAggregate.execute` path — the
same path the CLI surface uses — so telemetry view recording happens
identically through both entry points.

## Backlog Status

### DS-MCP-001: Expose all `24` sac verbs as MCP tools

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `surface_mcp_command.py::SkillsMcpAdapter.list_tools`        |
|              | returns descriptors for all 24 verbs;                          |
|              | `execute_tool` dispatches to `ISkillsAggregate.execute`.      |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-MCP-002: No capability import on the surface

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsMcpAdapter` imports only `ISkillsAggregate`,          |
|              | `SkillsRequest`, `SkillsOp`, `SkillsResult`, `SkillQuery`;   |
|              | composition root injects capabilities into the aggregate.    |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-MCP-003: Reachable from the root entry layer

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `root_cli_entry.py` imports `SkillsMcpAdapter` from           |
|              | `mcp.src.surface_mcp_command`, making the surface reachable   |
|              | via the import graph (satisfies AES506).                     |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-MCP-004: Agent-readable result contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `execute_tool` returns a stable envelope (`ok`, `content`    |
|              | with a single text block) drawn from `SkillsResult`; state   |
|              | is conveyed by the textual payload, never by spatial layout  |
|              | or color.                                                    |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| Design       | Visual & interaction contract              | [DESIGN.md](DESIGN.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
