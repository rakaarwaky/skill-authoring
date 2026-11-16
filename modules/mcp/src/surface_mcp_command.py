"""Skills-design MCP adapter (AES surface layer).

MCP adapter exposing every ``sac`` skill command as an MCP tool with
1:1 CLI equivalence. Each MCP tool delegates to the composed
``ISkillsAggregate.execute`` path — the same path the CLI uses — and
therefore triggers the same telemetry view recording on success.

The public entry point is ``SkillsMcpAdapter``.
"""
from __future__ import annotations

from shared.src.common.taxonomy_common_error import SkillsUsageError
from shared.src.design.contract_design_aggregate import ISkillsAggregate
from shared.src.design.taxonomy_design_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
)
from shared.src.design.taxonomy_design_response import (
    SkillsExitCode,
    SkillsResult,
)

__all__ = ["SkillsMcpAdapter"]


class SkillsMcpAdapter:
    """MCP adapter: maps sac verbs to MCP tools, 1:1 with the CLI.

    Every tool delegates to the composed aggregate — the same execution
    path the CLI surface uses — so telemetry view recording happens
    identically through both entry points.
    """

    def __init__(self, aggregate: ISkillsAggregate) -> None:
        self._aggregate = aggregate

    # ── Tool registry ───────────────────────────────────────────────

    def list_tools(self) -> list[dict]:
        """Return MCP tool descriptors, one per sac verb (19 tools).

        Each descriptor carries a draft-07 ``inputSchema`` so MCP clients
        can validate arguments before they reach the aggregate.
        """
        return [
            {
                "name": "sac_list",
                "description": "List all skills in the pack",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "sac_read",
                "description": "Print a skill's SKILL.md",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill": {"type": "string", "description": "Skill name to read"},
                    },
                    "required": ["skill"],
                },
            },
            {
                "name": "sac_export",
                "description": "Export a skill folder to a single Markdown file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill": {"type": "string", "description": "Skill name to export"},
                    },
                    "required": ["skill"],
                },
            },
            {
                "name": "sac_lint",
                "description": "Lint scan all skills",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Filter lint scan by category",
                        },
                    },
                },
            },
            {
                "name": "sac_catalog",
                "description": "Build and/or print catalog.json",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "check": {
                            "type": "boolean",
                            "description": "Check if catalog.json is in sync",
                        },
                    },
                },
            },
            {
                "name": "sac_discover",
                "description": "Search the catalog",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {
                            "type": "integer",
                            "default": 20,
                            "description": "Max results to return",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "sac_move",
                "description": "Move a skill to a category",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill": {"type": "string", "description": "Skill name to move"},
                        "target": {"type": "string", "description": "Target category folder"},
                        "apply": {
                            "type": "boolean",
                            "description": "Execute the move instead of a dry run",
                        },
                    },
                    "required": ["skill", "target"],
                },
            },
            {
                "name": "sac_archive",
                "description": "Archive a skill",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill": {"type": "string", "description": "Skill name to archive"},
                        "apply": {
                            "type": "boolean",
                            "description": "Execute the archive instead of a dry run",
                        },
                    },
                    "required": ["skill"],
                },
            },
            {
                "name": "sac_create",
                "description": "Create a skill or category",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill": {
                            "type": "string",
                            "description": "Skill name to create (kind=skill)",
                        },
                        "category": {
                            "type": "string",
                            "description": "Parent category folder for the new skill",
                        },
                        "kind": {
                            "type": "string",
                            "enum": ["skill", "category"],
                            "description": "Create a skill or a bare category",
                        },
                        "description": {
                            "type": "string",
                            "description": "Skill description written into SKILL.md frontmatter",
                        },
                        "apply": {
                            "type": "boolean",
                            "description": "Write the new skill or category to disk",
                        },
                    },
                    "required": ["skill", "category"],
                },
            },
            {
                "name": "sac_status",
                "description": "Show per-skill lifecycle states",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Optional skill name filter",
                        },
                    },
                },
            },
            {
                "name": "sac_usage",
                "description": "Show usage telemetry rows",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Optional skill name filter"},
                        "verb": {
                            "type": "string",
                            "enum": ["report", "seed", "reanchor"],
                            "description": "Usage sub-verb to run",
                        },
                    },
                },
            },
            {
                "name": "sac_run",
                "description": "Run automated state transitions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "apply": {
                            "type": "boolean",
                            "description": "Execute state transitions",
                        },
                    },
                },
            },
            {
                "name": "sac_pause",
                "description": "Pause automatic transitions",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "sac_resume",
                "description": "Resume automatic transitions",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "sac_pin",
                "description": "Pin a skill",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill": {"type": "string", "description": "Skill name to pin"},
                    },
                    "required": ["skill"],
                },
            },
            {
                "name": "sac_unpin",
                "description": "Unpin a skill",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill": {"type": "string", "description": "Skill name to unpin"},
                    },
                    "required": ["skill"],
                },
            },
            {
                "name": "sac_restore",
                "description": "Restore an archived skill",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill": {"type": "string", "description": "Skill name to restore"},
                        "category": {
                            "type": "string",
                            "description": "Target category folder for the restored skill",
                        },
                        "apply": {
                            "type": "boolean",
                            "description": "Execute the restore instead of a dry run",
                        },
                    },
                    "required": ["skill"],
                },
            },
            {
                "name": "sac_prune",
                "description": "Archive idle skills and purge old archives",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Archive skills idle for at least N days",
                        },
                        "purge_days": {
                            "type": "integer",
                            "description": "Purge archives older than N days",
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "Report what would be pruned without mutating",
                        },
                    },
                },
            },
            {
                "name": "sac_ledger",
                "description": "View or compact audit ledger",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "Ledger action to run"},
                        "skill": {"type": "string", "description": "Optional skill name filter"},
                    },
                },
            },
        ]

    def execute_tool(self, name: str, arguments: dict) -> dict:
        """Dispatch an MCP tool call to the aggregate and return an MCP result."""
        tool_name = name.removeprefix("sac_")
        result = self._dispatch(tool_name, arguments)
        rendered_text = self._render_tool_result(arguments, result)
        return {
            "ok": result.ok,
            "content": [
                {
                    "type": "text",
                    "text": rendered_text,
                }
            ],
        }

    # ── Result rendering (1:1 CLI equivalence, no ANSI codes) ──────

    def _render_tool_result(self, args: dict, result: SkillsResult) -> str:
        """Dispatch rendering on result.op; emit all payload channels."""
        if not result.ok:
            return result.message or f"{result.op}: exit {result.exit_code}"

        if result.op == SkillsOp.LIST:
            return self._render_list_records(result.records)
        if result.op == SkillsOp.READ:
            return self._render_read_content(result, args.get("skill", args.get("query", "")))
        if result.op == SkillsOp.STATUS:
            return self._render_status_records(result.records)
        if result.op == SkillsOp.USAGE:
            return self._render_usage_records(result.records)

        return result.message or f"{result.op}: exit {result.exit_code}"

    @staticmethod
    def _render_list_records(records: tuple) -> str:
        """Render skill records as a clean 2-column text table (no ANSI codes).

        Matches CLI ``_cmd_list`` format: SKILL padded to 28 chars,
        separator line, rows with truncated descriptions, optional tip
        line, and footer count.
        """
        rows = list(records)
        if not rows:
            return "No skills in the pack yet."

        lines = []
        lines.append("SKILL".ljust(28) + "DESCRIPTION")
        lines.append("-" * 28 + " " + "-" * 60)
        truncated = False
        for record in rows:
            desc = (record.description or "").replace("\n", " ")
            if len(desc) > 70:
                desc = desc[:69] + "…"
                truncated = True
            lines.append(record.name.ljust(28) + " " + desc)
        if truncated:
            lines.append("Tip: sac read <name> for full content")
        lines.append("")
        lines.append(f"{len(rows)} skills in the pack.")
        return "\n".join(lines)

    @staticmethod
    def _render_read_content(result: SkillsResult, name: str) -> str:
        """Return the raw SKILL.md content for a read operation."""
        if result.content is not None and result.content != "":
            return str(result.content)
        return result.message or f"Skill not found: {name}"

    @staticmethod
    def _render_status_records(records: tuple) -> str:
        """Render telemetry rows as lifecycle state lines (name: state (pinned))."""
        rows = list(records)
        lines = [f"[OK] status — {len(rows)} state row(s)"]
        for rec in rows:
            name = getattr(rec, "name", "unknown")
            state = getattr(rec, "state", "active")
            pinned = " (pinned)" if getattr(rec, "pinned", False) else ""
            lines.append(f"  {name}: {state}{pinned}")
        return "\n".join(lines)

    @staticmethod
    def _render_usage_records(records: tuple) -> str:
        """Render usage telemetry rows (name: views=N uses=N state=X)."""
        rows = list(records)
        lines = [f"[OK] usage — {len(rows)} skill row(s)"]
        for rec in rows:
            name = getattr(rec, "name", "unknown")
            views = getattr(rec, "views", 0)
            uses = getattr(rec, "uses", 0)
            state = getattr(rec, "state", "active")
            lines.append(f"  {name}: views={views} uses={uses} state={state}")
        return "\n".join(lines)

    # ── Internals ──────────────────────────────────────────────────

    def _op_from_tool(self, tool: str) -> SkillsOp:
        mapping = {
            "list": SkillsOp.LIST,
            "read": SkillsOp.READ,
            "export": SkillsOp.EXPORT,
            "lint": SkillsOp.LINT,
            "catalog": SkillsOp.CATALOG,
            "discover": SkillsOp.DISCOVER,
            "move": SkillsOp.MOVE,
            "archive": SkillsOp.ARCHIVE,
            "create": SkillsOp.CREATE,
            "status": SkillsOp.STATUS,
            "usage": SkillsOp.USAGE,
            "run": SkillsOp.RUN,
            "pause": SkillsOp.PAUSE,
            "resume": SkillsOp.RESUME,
            "pin": SkillsOp.PIN,
            "unpin": SkillsOp.UNPIN,
            "restore": SkillsOp.RESTORE,
            "prune": SkillsOp.PRUNE,
            "ledger": SkillsOp.LEDGER,
        }
        try:
            return mapping[tool]
        except KeyError:
            raise SkillsUsageError(f"Unknown skills subcommand: {tool}")

    def _dispatch(self, tool: str, args: dict) -> SkillsResult:
        try:
            op = self._op_from_tool(tool)
        except SkillsUsageError as failure:
            return SkillsResult(
                ok=False,
                op=SkillsOp.LIST,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=str(failure),
            )
        query = SkillQuery(args.get("query", args.get("skill", "")))
        flags = self._flags(tool, args)
        apply_ = bool(args.get("apply", False))
        request = SkillsRequest(op=op, query=query, flags=flags, apply=apply_)
        return self._aggregate.execute(request)

    @staticmethod
    def _flags(tool: str, args: dict) -> dict:
        flags: dict = {}
        if tool == "lint" and args.get("category"):
            flags["category"] = args["category"]
        if tool == "catalog":
            flags["build"] = "1"
            flags["read"] = "1"
        if tool == "discover":
            flags["limit"] = str(args.get("limit", 20))
        if tool == "move" and args.get("target"):
            flags["target"] = args["target"]
        if tool == "create":
            for key in ("kind", "category", "description", "when_to_use", "argument_hint", "body"):
                if args.get(key):
                    flags[key] = args[key]
            if args.get("force"):
                flags["force"] = "1"
        if tool == "prune":
            for key in ("days", "purge_days", "dry_run"):
                if args.get(key) is not None:
                    flags[key] = str(args[key])
        return flags


__all__ = ["SkillsMcpAdapter"]
