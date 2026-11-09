"""Skills-design MCP adapter surface (AES surface layer).

Re-exports ``SkillsMcpAdapter`` from ``surface_mcp_command`` so the
package surface and the command module share one implementation — no
duplication between the barrel and the module.
"""

from .surface_mcp_command import SkillsMcpAdapter

__all__ = ["SkillsMcpAdapter"]

_layer_symbols = {
    "SkillsMcpAdapter": SkillsMcpAdapter,
}
