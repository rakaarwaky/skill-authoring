"""Skills-design CLI entry (AES root layer).

The single entry point for ``sac`` design-side verbs: parses argv,
builds a ``SkillsContainer``, injects the aggregate into the surface, and
returns the process exit code. This is the only module that knows both
the root and surface packages exist and composes them at the call site.

Dispatch table:
  - <list|read|export|lint|catalog|discover|move|archive|create|status|usage|run|pause|resume|pin|unpin|restore|list-unmanaged|list-archived|prune> [flags]
"""

from __future__ import annotations

import sys

from shared.src.storage.utility_path_bootstrap import bootstrap_ns_roots

# Explicit namespace-root path bootstrap at entry (replaces import-time
# side effect plus discard of _REPO_ROOT). AES504 consumers that need
# _REPO_ROOT itself can import it from utility_path_bootstrap directly.
bootstrap_ns_roots()

from cli.src.surface_skills_command import cmd_skills
from mcp.src.surface_mcp_command import SkillsMcpAdapter
from root_skills_container import default_aggregate

__all__ = ["create_mcp_adapter", "main"]


def create_mcp_adapter() -> SkillsMcpAdapter:
    """Build the MCP adapter wired to the composed aggregate.

    This is the entry-layer reachability seam for the mcp surface (AES506):
    the only module that knows both the root and surface packages exist and
    composes them at the call site.
    """
    return SkillsMcpAdapter(default_aggregate())


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``sac <verb> [flags]``."""
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: sac <list|read|export|lint|catalog|discover|move|archive|create|status|usage|pin|unpin|restore|list-unmanaged|list-archived|prune> [flags]", file=sys.stderr)
        return 2
    # The skill pack on a CI host is this repo's own `skills/` tree, not
    # $HOME/.agents/skills: checkout lands under the runner workspace, so the
    # default pack root would find no skills and the drift gate would always
    # fail. The catalog check runs against the in-repo tree when $HOME has no
    # pack (CLI verbs keep using the default for interactive use).
    from pathlib import Path as _Path

    default_root = _Path(__file__).resolve().parents[4] / "skills"
    if default_root.is_dir():
        aggregate = default_aggregate(default_root=default_root)
    else:
        aggregate = default_aggregate()
    return cmd_skills(args, aggregate)


if __name__ == "__main__":
    raise SystemExit(main())
