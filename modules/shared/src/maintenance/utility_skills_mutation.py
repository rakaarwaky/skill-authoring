"""Skills mutation utilities (AES utility layer).

Shared helpers for the mover, archiver, and creator capabilities:
skill-dir resolution, category-name validation, containment assertion,
and the weed / repair report generators. These were split out of the
retired ``capabilities_skills_mutator`` so each mutation capability can
depend on the shared kernel without a sibling import.

The skill-tree walkers and parsers this file needs are inlined here
(AES201: utility files never import one another). All domain types come
from ``shared.src.common`` — no sibling domain imports.
"""
from __future__ import annotations

import json
import os
import posixpath
import re
from collections.abc import Iterable, Iterator
from pathlib import Path

from shared.src.common.taxonomy_common_constant import (
    ARCHIVE_DIRNAME,
    ASSETS_MARKER_FILENAME,
    CATEGORY_DESCRIPTION_FILENAME,
    IGNORED_CATEGORY_DIRS,
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
)
from shared.src.common.taxonomy_common_entity import CategorySummary, SkillEntry
from shared.src.common.taxonomy_common_error import (
    CategoryNameError,
    SkillNotFoundError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.common.taxonomy_common_vo import MutationPlan, MutationStep

__all__ = [
    "archive_root",
    "assert_within_root",
    "atomic_write_json",
    "category_dirs",
    "category_summaries",
    "clean_one_line",
    "iter_skill_mds",
    "missing_category_descriptions",
    "name_mismatch_repairs",
    "parse_frontmatter",
    "plan_repair",
    "plan_weed",
    "read_skill_md",
    "relpath",
    "resolve_skill_dir",
    "sanitize_skill_name",
    "skill_entries",
    "validate_category_name",
]


def cross_process_lock(handle: object) -> None:
    """Take an exclusive, blocking cross-process lock on *handle*.

    Uses ``fcntl.flock`` on POSIX and ``msvcrt.locking`` on Windows.
    """
    try:
        import fcntl as _fcntl
    except ImportError:  # pragma: no cover - POSIX only
        _fcntl = None
    try:
        import msvcrt as _msvcrt
    except ImportError:  # pragma: no cover - Windows only
        _msvcrt = None

    if _fcntl is not None:
        _fcntl.flock(handle.fileno(), _fcntl.LOCK_EX)
    elif _msvcrt is not None:
        handle.flush()
        _msvcrt.locking(handle.fileno(), _msvcrt.LK_LOCK, (1 << 31) - 1)


def clean_one_line(value: object) -> str:
    """Collapse whitespace to single spaces and strip the edges."""
    return " ".join(str(value).split()).strip()


def relpath(path: Path, skills_root: Path) -> str:
    """A skills-root-relative path when possible, else the absolute one."""
    try:
        return str(path.relative_to(skills_root))
    except ValueError:
        return str(path)


def category_dirs(skills_root: Path) -> Iterator[Path]:
    """Yield category directories, skipping hidden/ignored names."""
    if not skills_root.is_dir():
        raise SkillsRootError(f"Skills root does not exist: {skills_root}")

    for path in sorted(skills_root.iterdir()):
        if path.is_symlink() or not path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        if path.name in IGNORED_CATEGORY_DIRS:
            continue
        yield path


def parse_frontmatter(path: Path) -> dict[str, object]:
    """Parse YAML frontmatter from ``path``; returns {} when absent/broken.

    Optional PyYAML pass, then a minimal single-line ``key: value``
    fallback.
    """
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}

    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}

    parts = stripped.split("---", 2)
    if len(parts) < 3:
        return {}

    fm_text = parts[1]

    data: dict[str, object] = {}
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        if line != line.lstrip():
            continue
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if not key or value in {"", "|", ">", "|-", ">-"}:
            continue
        if value.startswith(("[", "{", "- ")):
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        data[key] = value

    return data


def skill_entries(skills_root: Path) -> list[SkillEntry]:
    """All discoverable skills: ``category/*/SKILL.md`` with frontmatter."""
    entries: list[SkillEntry] = []

    for category in category_dirs(skills_root):
        for skill_md in sorted(category.glob("*/SKILL.md")):
            skill_dir = skill_md.parent
            frontmatter = parse_frontmatter(skill_md)

            entries.append(
                SkillEntry(
                    skill=skill_dir.name,
                    frontmatter_name=clean_one_line(
                        frontmatter.get("name", skill_dir.name)
                    ),
                    category=category.name,
                    description=clean_one_line(frontmatter.get("description", "")),
                    when_to_use=clean_one_line(frontmatter.get("when-to-use", "")),
                    path=f"{category.name}/{skill_dir.name}",
                )
            )

    return entries


def category_summaries(
    entries: Iterable[SkillEntry], skills_root: Path
) -> list[CategorySummary]:
    """Per-category description state and skill counts."""
    entries = list(entries)
    summaries: list[CategorySummary] = []

    for category in category_dirs(skills_root):
        desc_file = category / CATEGORY_DESCRIPTION_FILENAME
        description = ""
        exists = desc_file.exists()

        if exists:
            frontmatter = parse_frontmatter(desc_file)
            description = clean_one_line(frontmatter.get("description", ""))

        skill_count = sum(1 for entry in entries if entry.category == category.name)

        summaries.append(
            CategorySummary(
                category=category.name,
                description=description,
                description_file_exists=exists,
                skill_count=skill_count,
            )
        )

    return summaries


# ─── Tree walker readers (local; utility files stay independent, AES201) ──


def default_pack_root() -> Path:
    """Return the repo's ``skills/`` pack (the SSOT for all skills)."""
    return Path(__file__).resolve().parents[7]


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


def read_skill_md(skill_md: Path) -> str | None:
    """Read a SKILL.md, returning None when it cannot be read."""
    try:
        return skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def is_valid_skill_name(name: str) -> bool:
    """The name-format predicate for skill directory names."""
    return bool(NAME_RE.match(name)) and "--" not in name and NAME_MIN <= len(name) <= NAME_MAX


def sanitize_skill_name(raw: str, fallback: str) -> str:
    """Convert frontmatter name into a safe directory name (prevents path traversal)."""
    raw = (raw or "").strip().replace("\\", "/")
    raw = posixpath.basename(raw)
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-")
    if not name:
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", fallback).strip(".-") or "skill"
    return name[:64]


# ─── Private helpers ──────────────────────────────────────────────────


def _assets_container(skills_root: Path) -> set[str]:
    """Category names that carry a declared DM2 asset-container marker."""
    declared: set[str] = set()
    for category in category_dirs(skills_root):
        marker = category / ASSETS_MARKER_FILENAME
        if not marker.is_file():
            continue
        frontmatter = parse_frontmatter(marker)
        if frontmatter.get("kind") == "assets":
            declared.add(category.name)
    return declared


def _yaml_quote(value: object) -> str:
    """Quote a YAML scalar the way the original ``librarian.py`` did."""
    return json.dumps(str(value), ensure_ascii=False)


# ─── Public mutation helpers ──────────────────────────────────────────


def archive_root(skills_root: Path) -> Path:
    """The archive tree for a skills root."""
    return skills_root / ARCHIVE_DIRNAME


def assert_within_root(path: Path, root: Path) -> None:
    """Fail closed when a computed destination escapes the skills root."""
    try:
        contained = path.resolve().is_relative_to(root.resolve())
    except OSError:
        contained = False
    if not contained:
        raise SkillsUsageError(f"Refusing to write outside the skills root: {path}")


def write_category_description(
    category: Path, description: str, force: bool = False
) -> bool:
    """Write ``category/DESCRIPTION.md``; keep an existing one unless ``force``."""
    desc_file = category / CATEGORY_DESCRIPTION_FILENAME

    if desc_file.exists() and not force:
        return False

    desc_file.write_text(
        f"---\ndescription: {_yaml_quote(description)}\n---\n",
        encoding="utf-8",
    )
    return True


def name_mismatch_repairs(skills_root: Path) -> list[tuple[Path, str]]:
    """The ``(skill_md, expected_name)`` pairs a repair would rewrite."""
    pairs: list[tuple[Path, str]] = []

    for entry in skill_entries(skills_root):
        if entry.frontmatter_name != entry.skill:
            pairs.append((skills_root / entry.path / "SKILL.md", entry.skill))

    return pairs


def missing_category_descriptions(skills_root: Path) -> list[Path]:
    """The category dirs whose ``DESCRIPTION.md`` a repair would create.

    Declared DM2 asset containers are exempt: a repair never writes a
    ``DESCRIPTION.md`` into an asset container.
    """
    assets = _assets_container(skills_root)
    return [
        category / CATEGORY_DESCRIPTION_FILENAME
        for category in category_dirs(skills_root)
        if not (category / CATEGORY_DESCRIPTION_FILENAME).exists()
        and category.name not in assets
    ]


def validate_category_name(name: str) -> None:
    """The category-shape gate, verbatim from the original ``librarian.py``."""
    if not NAME_RE.match(name) or "--" in name or not (NAME_MIN <= len(name) <= NAME_MAX):
        raise CategoryNameError(
            "Category name must be lowercase a-z, 0-9, hyphens, 2-64 chars, "
            "no leading/trailing hyphen or double hyphen."
        )


def resolve_skill_dir(skill_ref: str, skills_root: Path) -> Path:
    """Resolve a ``category/skill`` or bare ``skill`` reference to its folder.

    Verbatim resolution order from the original ``librarian.py``:
    absolute paths; then ``category/skill`` under the root; then a bare
    name searched across every category; then the cwd-relative path;
    then the root-relative path. The first candidate that is a directory
    containing ``SKILL.md`` wins.
    """
    p = Path(skill_ref)
    candidates: list[Path] = []

    if p.is_absolute():
        candidates.append(p)
    else:
        if len(p.parts) == 2:
            candidates.append(skills_root / p)

        if len(p.parts) == 1:
            for category in category_dirs(skills_root):
                candidates.append(category / p)

        candidates.append(Path.cwd() / p)
        candidates.append(skills_root / p)

    for candidate in candidates:
        candidate = Path(candidate).resolve()
        if candidate.is_dir() and (candidate / "SKILL.md").exists():
            return candidate

    raise SkillNotFoundError(
        f"Could not find skill directory with SKILL.md: {skill_ref}"
    )


def plan_weed(root: Path) -> MutationPlan:
    """The weeding report body, without the ``Weeding report:`` header."""
    skills_root = root
    entries = skill_entries(skills_root)
    summaries = category_summaries(entries, skills_root)
    assets = _assets_container(skills_root)

    name_map: dict[str, list[str]] = {}
    desc_map: dict[str, list[str]] = {}

    for entry in entries:
        name_map.setdefault(entry.skill, []).append(entry.path)
        if entry.description:
            desc_map.setdefault(entry.description, []).append(entry.path)

    lines: list[str] = []

    for name, paths in sorted(name_map.items()):
        if len(paths) > 1:
            lines.append(
                f"- duplicate-skill-name: '{name}' appears in: "
                f"{', '.join(sorted(paths))}"
            )

    for description, paths in sorted(desc_map.items()):
        if len(paths) > 1:
            short = description if len(description) <= 80 else description[:77] + "..."
            lines.append(
                f"- duplicate-description: '{short}' appears in: "
                f"{', '.join(sorted(paths))}"
            )

    for summary in summaries:
        if summary.category in assets:
            continue
        if summary.skill_count == 0:
            lines.append(f"- empty-category: {summary.category}")
        if not summary.description_file_exists:
            lines.append(f"- missing-category-description: {summary.category}")

    return MutationPlan(kind="weed", lines=tuple(lines), root=skills_root)


def plan_repair(root: Path) -> MutationPlan:
    """The mechanical repairs the old ``librarian.py repair`` applied."""
    skills_root = root
    steps: list[MutationStep] = []
    lines: list[str] = []

    for skill_md, expected_name in name_mismatch_repairs(skills_root):
        line = f"Fixed name in {skill_md.parent.name}/SKILL.md"
        lines.append(line)
        steps.append(
            MutationStep(
                action="rewrite-name",
                description=line,
                source=skill_md,
                value=expected_name,
            )
        )

    for desc_file in missing_category_descriptions(skills_root):
        category = desc_file.parent.name
        description = f"Skills in the {category} category."
        line = (
            f"Created {category}/DESCRIPTION.md "
            f"(would write: {_yaml_quote(description)})"
        )
        lines.append(line)
        steps.append(
            MutationStep(
                action="create-description",
                description=line,
                destination=desc_file,
                value=description,
            )
        )

    return MutationPlan(
        kind="repair",
        steps=tuple(steps),
        lines=tuple(lines),
        root=skills_root,
    )


def atomic_write_json(path: Path, payload: object) -> None:
    """Atomically write ``payload`` as JSON to ``path`` (temp + os.replace).

    Cross-process lock on POSIX via ``fcntl.flock`` and on Windows via
    ``msvcrt.locking`` so concurrent writers never interleave or tear
    the file. Fails closed: I/O or lock failures raise ``OSError``
    (the same error type neighboring mutation helpers raise) rather than
    silently corrupting a sidecar.
    """
    if path.parent.is_dir():
        tmp = path.with_name(path.name + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as handle:
                cross_process_lock(handle)
                json.dump(payload, handle, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, path)
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
    else:
        raise OSError(f"Cannot write JSON outside a directory: {path.parent}")
