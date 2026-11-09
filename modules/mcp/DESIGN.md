# DESIGN — mcp

## Design Overview

The skills MCP adapter surface is a thin MCP adapter layer: it exposes
every `sac` skill command as an MCP tool with 1:1 CLI equivalence and
delegates each call to the aggregate's single `execute` entry point —
the same path the CLI surface uses. The surface kind is an **MCP
adapter**: instead of parsing raw argv into a typed `SkillsRequest`,
it maps each MCP tool name to its `SkillsOp` and handoff-arguments to
the same `SkillsRequest` shape, then hands it to `ISkillsAggregate.execute`.
No surface module imports a capability module directly; the aggregate is
injected by the composition root.

**Surface kind:** MCP adapter. The surface publishes a tool registry
(`list_tools`) and a dispatcher (`execute_tool`); it does not own
lifecycle, storage, or discovery state — all state transitions flow
through the injected aggregate.

**Entry points:** `SkillsMcpAdapter` (class, public) exposes every `sac`
verb as an MCP tool, constructed with the composed `ISkillsAggregate`;
`SkillsMcpAdapter.list_tools` returns MCP tool descriptors, one per `sac`
verb (24 tools); `SkillsMcpAdapter.execute_tool` dispatches an MCP tool
call to the aggregate and returns an MCP result envelope (`ok`, `content`).

**Visible states:** the surface itself is stateless; visible states come
from the aggregate's `SkillsResult.ok` flag and message, exposed as the
MCP result envelope — `ok: true` means the verb executed cleanly with
`content` carrying the verb's textual output; `ok: false` means the verb
reported an issue with `content` carrying the `SkillsResult` message.

## Design Requirements

### DS-MCP-001: Expose `sac` verbs as MCP tools, 1:1 with the CLI

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| 24 tools | One MCP tool per `sac` verb (list, read, lint, catalog, discover, move, archive, create, status, usage, run, pause, resume, pin, unpin, lock, unlock, restore, prune, purge, adopt, backup, rollback, ledger) | `SkillsOp` | `ISkillsAggregate.execute` |

Each MCP tool maps to its `SkillsOp` via `_op_from_tool` and routes
through `ISkillsAggregate.execute`, so the MCP path and the CLI path
share one execution path and identical telemetry view recording.

### DS-MCP-002: No capability import on the surface

Every surface method talks only to `ISkillsAggregate`. The composition
root injects concrete capabilities into the aggregate at construction
time; the surface never knows concrete implementations.

### DS-MCP-003: Reachable from the root entry layer

`root_cli_entry.py` imports `SkillsMcpAdapter` from
`mcp.src.surface_mcp_command`, making the surface reachable via the
import graph from an entry file (satisfies AES506: surface must be
reachable from an entry point).

### DS-MCP-004: Agent-readable result contract

Consumers are MCP agents, not humans. `execute_tool` returns a stable
envelope (`ok`, `content` with a single text block) drawn from
`SkillsResult`; state is conveyed by the textual payload, never by
spatial layout or color.

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | Business goals, user stories, and scope | [PRD.md](../../../../../PRD.md) |
| Backlog | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap | Timeline, phasing, and dependencies | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
