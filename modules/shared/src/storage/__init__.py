"""Skills-design shared kernel — storage layer.

Filesystem helpers for reading the skill pack: locate ``SKILL.md`` files,
parse frontmatter, read body text, bootstrap paths, and default pack root.
"""
from shared.src.storage.utility_path_bootstrap import _NS_ROOTS, _REPO_ROOT
from shared.src.storage.utility_skill_pack import (
    default_pack_root,
    parse_skill_frontmatter,
    read_skill_md,
    sanitize_skill_name,
)

__all__ = [
    "_NS_ROOTS",
    "_REPO_ROOT",
    "default_pack_root",
    "parse_skill_frontmatter",
    "read_skill_md",
    "sanitize_skill_name",
]
