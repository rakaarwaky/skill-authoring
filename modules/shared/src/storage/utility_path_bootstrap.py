"""Bootstrap sys.path for the standalone skills-design CLI app.

The ``skills_design`` package lives under this dir; the repo root stays
on the path so the orchestrator-owned composition root
(``modules.root_cli_entry``) and the shared modules remain importable.
Each tree bootstraps only its own namespace root — no shared skill
package dir exists any more (AES702 independent packages).
"""
import sys
from pathlib import Path

# Repo markers recognized by ``find_repo_root``.
_REPO_MARKERS = (".git", "pyproject.toml")


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from *start* (default: this file's directory) until a repo marker is found.

    The first ancestor directory containing ``.git`` or ``pyproject.toml`` wins.
    Raises ``SkillsUsageError`` when no marker exists anywhere up the tree.
    """
    from shared.src.common.taxonomy_common_error import SkillsUsageError

    current = (start or Path(__file__)).resolve()
    for ancestor in (current, *current.parents):
        if any((ancestor / marker).exists() for marker in _REPO_MARKERS):
            return ancestor
    raise SkillsUsageError(f"No repo marker ({', '.join(_REPO_MARKERS)}) found from {current}")


_REPO_ROOT = find_repo_root()
_NS_ROOTS = [
    Path(__file__).resolve().parent,
    _REPO_ROOT,
]


def bootstrap_ns_roots() -> None:
    """Insert this tree's namespace roots onto sys.path (explicit entry-point call)."""
    for _ns in _NS_ROOTS:
        _ns_str = str(_ns)
        if _ns.is_dir() and _ns_str not in sys.path:
            sys.path.insert(0, _ns_str)


bootstrap_ns_roots()
