"""Skills exporter capability (AES capabilities layer).

Exports a skill folder into a single Markdown document saved at
``~/.agents/skills/.export/<namaskill>.md``. Implements
``ISkillsExportProtocol`` from ``shared/src/storage/contract_storage_protocol.py``.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.common.taxonomy_common_vo import SkillName, SkillsRoot
from shared.src.common.utility_common_skills import (
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

        export_dir = Path.home() / ".agents" / "skills" / ".export"
        export_dir.mkdir(parents=True, exist_ok=True)

        target_files = self._collect_skill_files(skill_dir)
        # Filter to supported text extensions only, skipping binary/cache noise
        supported_exts = {".md", ".py", ".rs", ".ts", ".json", ".sh", ".toml"}
        target_files = [
            (rp, fp) for rp, fp in target_files if fp.suffix.lower() in supported_exts
        ]
        sections: list[str] = []
        for rel_path, file_path in target_files:
            text = file_path.read_text(encoding="utf-8", errors="replace").rstrip()
            if text:
                sections.append(f"## {rel_path}\n\n{text}\n")
            else:
                sections.append(f"## {rel_path}\n")

        index_section = self._format_index_section(skill_name, target_files)
        out_content = index_section + "\n" + "\n".join(sections)
        out_file = export_dir / f"{skill_name}.md"
        out_file.write_text(out_content, encoding="utf-8")
        return out_file

    # ─── Block 3: Module Helpers ───
    def _format_index_section(
        self,
        skill_name: str,
        target_files: list[tuple[str, Path]],
    ) -> str:
        """Format the Index section listing all exported file relative paths."""
        lines = [
            f"# {skill_name}",
            "",
            "## Index",
            "",
        ]
        for rel_path, _ in target_files:
            lines.append(f"- `{rel_path}`")
        lines.append("")
        lines.append("---")
        lines.append("")
        return "\n".join(lines)

    def _is_hidden(self, file_path: Path, base_dir: Path) -> bool:
        """True when any component of *file_path* relative to *base_dir* is dotted."""
        return any(
            part.startswith(".") for part in file_path.relative_to(base_dir).parts
        )

    def _collect_skill_files(self, skill_dir: Path) -> list[tuple[str, Path]]:
        """Collect key files: SKILL.md, reference/, template/, scripts/, README.md."""
        files: list[tuple[str, Path]] = []

        skill_md = skill_dir / "SKILL.md"
        if skill_md.is_file() and not self._is_hidden(skill_md, skill_dir):
            files.append(("SKILL.md", skill_md))

        subdirs = [
            ("reference", "references"),
            ("template", "templates"),
            ("scripts",),
            ("persona",),
        ]
        for group in subdirs:
            for sub_name in group:
                sub_path = skill_dir / sub_name
                if sub_path.is_dir():
                    for item in sorted(sub_path.rglob("*")):
                        if item.is_file() and not self._is_hidden(item, sub_path):
                            rel_posix = item.relative_to(skill_dir).as_posix()
                            files.append((rel_posix, item))

        readme = skill_dir / "README.md"
        if readme.is_file() and not self._is_hidden(readme, skill_dir):
            files.append(("README.md", readme))

        return files
