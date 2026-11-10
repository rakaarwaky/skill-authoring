"""Skills-design CLI entry (AES root layer).

The single entry point for ``sac`` design-side verbs: parses argv,
builds a ``SkillsContainer``, injects the aggregate into the surface, and
returns the process exit code. This is the only module that knows both
the root and surface packages exist and composes them at the call site.

Dispatch table:
  - <list|read|lint|catalog|discover|move|archive|create> [flags]
"""

from __future__ import annotations

import sys

from shared.src.storage.utility_path_bootstrap import bootstrap_ns_roots

# Explicit namespace-root path bootstrap at entry (replaces import-time
# side effect plus discard of _REPO_ROOT). AES504 consumers that need
# _REPO_ROOT itself can import it from utility_path_bootstrap directly.
bootstrap_ns_roots()

from cli.src.surface_skills_command import cmd_skills
from root_skills_container import default_aggregate


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``sac <verb> [flags]``."""
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: sac <list|read|lint|catalog|discover|move|archive|create|status|usage|run|pause|resume|pin|unpin|lock|unlock|restore|list-unmanaged|list-archived|prune|purge|adopt|backup|rollback|ledger> [flags]", file=sys.stderr)
        return 2
    aggregate = default_aggregate()
    return cmd_skills(args, aggregate)


if __name__ == "__main__":
    raise SystemExit(main())
