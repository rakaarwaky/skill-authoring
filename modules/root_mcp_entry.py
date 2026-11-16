"""MCP stdio server entry (AES root layer).

Single entry point for the skill-authoring MCP stdio server: bootstraps
namespace roots, wires the ``SkillsMcpAdapter`` to the composed aggregate,
and runs the MCP stdio transport. Mirrors ``root_cli_entry.py`` for the CLI.

The public entry point is ``main``; ``create_mcp_adapter`` is the
composition-root seam (AES506) that makes the surface reachable from an
entry file.
"""

from __future__ import annotations

import sys
from pathlib import Path

# When invoked as ``modules/root_mcp_entry.py``, Python puts ``modules/`` on
# sys.path[0], so `import mcp` would resolve to the feature dir (modules/mcp)
# instead of the installed mcp library. Drop it here so the mcp.server /
# mcp.types import below lands on the installed package; modules/ is re-added
# to sys.path after that import.
_TOOLS_ROOT = Path(__file__).resolve().parents[1]  # .../skills/skill-authoring/tools
_MODULES = _TOOLS_ROOT / "modules"
_modules_on_path = str(_MODULES)
if _modules_on_path in sys.path:
    sys.path.remove(_modules_on_path)

from mcp.server import Server as _McpServer
from mcp.server.stdio import stdio_server as _stdio_server
from mcp.types import (
    CallToolResult as _CallToolResult,
    ListToolsResult as _ListToolsResult,
    TextContent as _TextContent,
    Tool as _Tool,
)

# Evict the installed mcp package from sys.modules so that re-adding modules/
# to the path lets `from mcp.src...` (used by root_cli_entry) resolve to
# modules/mcp instead of the installed package.
for _mod in ("mcp.server.stdio", "mcp.server", "mcp"):
    sys.modules.pop(_mod, None)

for _ns in (_TOOLS_ROOT, _MODULES):
    _ns_str = str(_ns)
    if _ns.is_dir() and _ns_str not in sys.path:
        sys.path.insert(0, _ns_str)

from shared.src.storage.utility_path_bootstrap import bootstrap_ns_roots

bootstrap_ns_roots()

# Each feature package places its source in modules/<feature>/src/ and
# imports siblings bare, so append each src/ dir to sys.path after modules/.
for _src in sorted(_MODULES.glob("*/src")):
    _ns_str = str(_src)
    if _ns_str not in sys.path:
        sys.path.append(_ns_str)

from modules.root_cli_entry import create_mcp_adapter

__all__ = ["create_mcp_adapter", "main"]


async def _list_tools(context=None, params=None) -> _ListToolsResult:
    """Return MCP tool descriptors, one per sac verb."""
    adapter = create_mcp_adapter()
    descriptors = adapter.list_tools()
    return _ListToolsResult(
        tools=[
            _Tool(
                name=d["name"],
                description=d.get("description", ""),
                input_schema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True,
                },
            )
            for d in descriptors
        ]
    )


async def _call_tool(context, params) -> _CallToolResult:
    """Dispatch an MCP tool call to the sac aggregate."""
    adapter = create_mcp_adapter()
    name = params.name
    args = params.arguments or {}
    result = adapter.execute_tool(name, args)
    text = result["content"][0]["text"] if result.get("content") else f"{result.get('op')}: exit {result.get('exit_code')}"
    return _CallToolResult(content=[_TextContent(type="text", text=text)])


def main() -> int:
    """Run the sac MCP stdio server."""
    server = _McpServer("sac", on_list_tools=_list_tools, on_call_tool=_call_tool)

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
