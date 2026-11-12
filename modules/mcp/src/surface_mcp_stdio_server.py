"""Stdio MCP server exposing every ``sac`` skill command as an MCP tool.

Wraps ``SkillsMcpAdapter`` (the same execution path the CLI uses) over the
MCP stdio transport so any MCP client — including Grok Build — can call
``sac list``/``read``/``lint``/``catalog``/``discover``/``move``/``archive``/
``create`` and all lifecycle verbs through a single stdio MCP server entry.

Bootstraps the skills-design namespace roots so all shared-kernel imports
resolve, then delegates each tool call to ``SkillsMcpAdapter.execute_tool``.

Usage (stdio):

    python3 modules/mcp/src/surface_mcp_stdio_server.py

Run from the skill-authoring tools root:

    cd skills/skill-authoring/tools
    python3 modules/mcp/src/surface_mcp_stdio_server.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# 1. Grab mcp.server / stdio_server from the INSTALLED mcp package BEFORE
#    modules/ lands on sys.path, because modules/mcp shadows it.
from mcp.server import Server as _McpServer  # noqa: E402
from mcp.server.stdio import stdio_server as _stdio_server  # noqa: E402
from mcp.types import TextContent as _TextContent, Tool as _Tool  # noqa: E402

# 2. Evict the installed mcp package from sys.modules so that adding
#    modules/ to the path lets `from mcp.src...` (used by root_cli_entry)
#    resolve to modules/mcp instead of the installed package.
for _mod in ("mcp.server.stdio", "mcp.server", "mcp"):
    sys.modules.pop(_mod, None)

# 3. Add namespace roots so shared.src.* and modules.* resolve first,
#    before any src/ dirs, so package imports (e.g. `import design`)
#    resolve to modules/<feature>/ not modules/<feature>/src/.
_TOOLS_ROOT = Path(__file__).resolve().parents[3]  # .../skills/skill-authoring/tools
_MODULES = _TOOLS_ROOT / "modules"

for _ns in (_TOOLS_ROOT, _MODULES):
    _ns_str = str(_ns)
    if _ns.is_dir() and _ns_str not in sys.path:
        sys.path.insert(0, _ns_str)

from shared.src.storage.utility_path_bootstrap import bootstrap_ns_roots  # noqa: E402

bootstrap_ns_roots()

# 4. Each feature package places its source in modules/<feature>/src/ and
#    imports siblings bare (e.g. `from agent_design_orchestrator import ...`),
#    so append each src/ dir to sys.path AFTER modules/ so bare imports
#    resolve without shadowing package resolution.
for _src in sorted(_MODULES.glob("*/src")):
    _ns_str = str(_src)
    if _ns_str not in sys.path:
        sys.path.append(_ns_str)

from modules.root_cli_entry import create_mcp_adapter  # noqa: E402

__all__ = ["main"]


def main() -> int:
    """Run the sac MCP stdio server."""
    adapter = create_mcp_adapter()
    server = _McpServer("sac")

    @server.list_tools()
    async def list_tools() -> list[_Tool]:
        """Return MCP tool descriptors, one per sac verb."""
        descriptors = adapter.list_tools()
        return [
            _Tool(
                name=d["name"],
                description=d.get("description", ""),
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True,
                },
            )
            for d in descriptors
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict | None) -> list[_TextContent]:
        """Dispatch an MCP tool call to the sac aggregate."""
        args = arguments or {}
        result = adapter.execute_tool(name, args)
        text = result.message or f"{result.op}: exit {result.exit_code}"
        return [_TextContent(type="text", text=text)]

    async def _run() -> None:
        async with _stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    import anyio

    anyio.run(_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
