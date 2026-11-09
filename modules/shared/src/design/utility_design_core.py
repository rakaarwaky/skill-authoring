"""Design-domain utility functions — stateless, pure, domain-agnostic.

Module-level functions only — no classes, no state.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.common.taxonomy_common_constant import (
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
)


def clean_one_line(value: object) -> str:
    """Collapse whitespace to single spaces and strip the edges."""
    return " ".join(str(value).split()).strip()


def is_valid_skill_name(name: str) -> bool:
    """The name-format predicate for skill directory names.

    ``NAME_RE`` match AND no double hyphen AND 2-64 chars.
    """
    return bool(NAME_RE.match(name)) and "--" not in name and NAME_MIN <= len(name) <= NAME_MAX


def default_pack_root() -> Path:
    """Return the repo's ``skills/`` pack (the SSOT for all skills)."""
    return Path(__file__).resolve().parents[7]


def relpath(path: Path, skills_root: Path) -> str:
    """A skills-root-relative path when possible, else the absolute one."""
    try:
        return str(path.relative_to(skills_root))
    except ValueError:
        return str(path)


__all__ = [
    "clean_one_line",
    "default_pack_root",
    "is_valid_skill_name",
    "relpath",
]

_layer_symbols = {
    "clean_one_line": clean_one_line,
    "default_pack_root": default_pack_root,
    "is_valid_skill_name": is_valid_skill_name,
    "relpath": relpath,
}
