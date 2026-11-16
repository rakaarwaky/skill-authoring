"""Skills exporter capability (AES capabilities layer).

Exports a skill folder into a single Markdown document saved at
``.export/<namaskill>.md`` under the pack root. Implements
``ISkillsExportProtocol`` from ``shared/src/storage/contract_storage_protocol.py``.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.common.taxonomy_common_vo import SkillName, SkillsRoot
from shared.src.common.utility_common_skills import (
    assert_within_root,
    default_pack_root,
    resolve_skill_dir,
)
from shared.src.storage.contract_storage_protocol import (
    ISkillsExportProtocol,
)

__all__ = ["SkillsExporter"]


# ─── Block 1: Module Declaration ───
class SkillsExporter(ISkillsExportProtocol):
    """Exports a skill folder into a single concatenated Markdown file."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ───
    def export(self, skill: SkillName, root: SkillsRoot | None = None) -> Path:
        """Export the skill folder for *skill* to a single Markdown file."""
        skills_root = Path(root) if root is not None else default_pack_root()
        skill_dir = resolve_skill_dir(str(skill), skills_root)
        skill_name = skill_dir.name

        export_dir = skills_root / ".export"
        assert_within_root(export_dir, skills_root)
        export_dir.mkdir(parents=True, exist_ok=True)

        target_files = self._collect_skill_files(skill_dir)
        sections: list[str] = []
        for rel_path, file_path in target_files:
            text = file_path.read_text(encoding="utf-8", errors="replace").rstrip()
            if text:
                sections.append(f"## {rel_path}\n\n{text}\n")
            else:
                sections.append(f"## {rel_path}\n")

        out_content = "\n".join(sections)
        out_file = export_dir / f"{skill_name}.md"
        assert_within_root(out_file, skills_root)
        out_file.write_text(out_content, encoding="utf-8")
        return out_file

    # ─── Block 3: Module Helpers ───
    def _collect_skill_files(self, skill_dir: Path) -> list[tuple[str, Path]]:
        """Collect key files: SKILL.md, reference/, template/, scripts/, README.md."""
        files: list[tuple[str, Path]] = []

        skill_md = skill_dir / "SKILL.md"
        if skill_md.is_file():
            files.append(("SKILL.md", skill_md))

        subdirs = [
            ("reference", "references"),
            ("template", "templates"),
            ("scripts",),
        ]
        for group in subdirs:
            for sub_name in group:
                sub_path = skill_dir / sub_name
                if sub_path.is_dir():
                    for item in sorted(sub_path.rglob("*")):
                        if item.is_file() and not item.name.startswith("."):
                            rel_posix = item.relative_to(skill_dir).as_posix()
                            files.append((rel_posix, item))

        readme = skill_dir / "README.md"
        if readme.is_file():
            files.append(("README.md", readme))

        return files
