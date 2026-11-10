"""Cross-feature utility functions (AES common layer).

Pure helpers consumed by more than one module domain
(discovery, design, storage, maintenance, governance, observability).
A module must import these from here rather than reaching into a sibling
domain's utility module — this is the anti-coupling seam.

Everything here is pure data / helpers with no imports from capability,
agent, root, or surface layers.
"""

from __future__ import annotations

import os
from pathlib import Path

from shared.src.common.taxonomy_common_constant import (
    ARCHIVE_DIRNAME,
    IGNORED_CATEGORY_DIRS,
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
)
from shared.src.common.taxonomy_common_error import (
    CategoryNameError,
    SkillNotFoundError,
    SkillsUsageError,
)

__all__ = [
    "assert_within_root",
    "default_pack_root",
    "find_repo_root",
    "find_skill_dir",
    "iter_skill_mds",
    "relpath",
    "resolve_skill_dir",
    "set_field",
    "validate_category_name",
]


# Repo markers recognized by ``find_repo_root``.
_REPO_MARKERS = (".git", "pyproject.toml")


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from *start* (default: this file's directory) until a repo marker is found.

    The first ancestor directory containing ``.git`` or ``pyproject.toml`` wins.
    Raises ``SkillsUsageError`` when no marker exists anywhere up the tree.
    """
    current = (start or Path(__file__)).resolve()
    for ancestor in (current, *current.parents):
        if any((ancestor / marker).exists() for marker in _REPO_MARKERS):
            return ancestor
    raise SkillsUsageError(f"No repo marker ({', '.join(_REPO_MARKERS)}) found from {current}")


def relpath(path: Path, skills_root: Path) -> str:
    """A skills-root-relative path when possible, else the absolute one."""
    try:
        return str(path.relative_to(skills_root))
    except ValueError:
        return str(path)


def assert_within_root(path: Path, root: Path) -> None:
    """Fail closed when a computed destination escapes the skills root."""
    try:
        contained = path.resolve().is_relative_to(root.resolve())
    except OSError:
        contained = False
    if not contained:
        raise SkillsUsageError(f"Refusing to write outside the skills root: {path}")


def find_skill_dir(skill: str, root: Path, in_archive: bool = False) -> Path | None:
    """Find a skill directory by name under root (optionally inside archive)."""
    search_root = root / ARCHIVE_DIRNAME if in_archive else root
    if not search_root.is_dir():
        return None
    matches: list[Path] = []
    for p in search_root.rglob("SKILL.md"):
        if p.parent.name == skill:
            matches.append(p.parent)
    return min(matches) if matches else None


def set_field(skill_dir: Path, field: str, value: object) -> None:
    """Set a single field on a skill's sidecar record."""
    record = _read_sidecar(skill_dir / ".usage.json")
    record[field] = value
    _write_sidecar(skill_dir / ".usage.json", record)


def resolve_skill_dir(skill_ref: str, skills_root: Path) -> Path:
    """Resolve a category/skill or bare skill reference to its folder."""
    p = Path(skill_ref)
    candidates: list[Path] = []

    if p.is_absolute():
        candidates.append(p)
    else:
        if len(p.parts) == 2:
            candidates.append(skills_root / p)

        if len(p.parts) == 1:
            for category in _category_dirs(skills_root):
                candidates.append(category / p)

        candidates.append(Path.cwd() / p)
        candidates.append(skills_root / p)

    for candidate in candidates:
        candidate = Path(candidate).resolve()
        if candidate.is_dir() and (candidate / "SKILL.md").exists():
            return candidate

    raise SkillNotFoundError(f"Could not find skill directory with SKILL.md: {skill_ref}")


def validate_category_name(name: str) -> None:
    if not NAME_RE.match(name) or "--" in name or not (NAME_MIN <= len(name) <= NAME_MAX):
        raise CategoryNameError(
            "Category name must be lowercase a-z, 0-9, hyphens, 2-64 chars, "
            "no leading/trailing hyphen or double hyphen."
        )


def default_pack_root() -> Path:
    """Return the default pack root path (repo root resolved via marker discovery)."""
    return find_repo_root()


def iter_skill_mds(pack_root: Path) -> list[Path]:
    """Return each ``SKILL.md`` in the pack as a sorted list, by path."""
    if not pack_root.is_dir():
        return []
    found: list[Path] = []
    for category in sorted(pack_root.iterdir()):
        if not category.is_dir() or category.is_symlink():
            continue
        if category.name.startswith("."):
            continue
        if category.name in IGNORED_CATEGORY_DIRS:
            continue
        found.extend(sorted(category.glob("*/SKILL.md")))
    return sorted(found)


# ── Private helpers (local to this utility module) ──


def _read_sidecar(path: Path) -> dict:
    import json

    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_sidecar(path: Path, record: dict) -> None:
    import json

    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _category_dirs(skills_root: Path):
    if not skills_root.is_dir():
        raise SkillsUsageError(f"Skills root does not exist: {skills_root}")

    for path in sorted(skills_root.iterdir()):
        if path.is_symlink() or not path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        if path.name in IGNORED_CATEGORY_DIRS:
            continue
        yield path
