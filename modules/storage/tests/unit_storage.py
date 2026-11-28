"""Storage-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from shared.src.common.taxonomy_common_constant import EXIT_USAGE
from shared.src.common.taxonomy_common_error import SkillNotFoundError
from shared.src.common.taxonomy_common_vo import SkillsRoot
from shared.src.storage.contract_storage_aggregate import (
    ISkillsStorageAggregate,
)
from shared.src.storage.taxonomy_storage_request import StorageRequest, StorageVerb
from storage.src.agent_storage_orchestrator import SkillsStorageAgent
from storage.src.capabilities_skills_archiver import SkillsArchiver
from storage.src.capabilities_skills_exporter import SkillsExporter
from storage.src.capabilities_skills_restore import SkillsRestore


class _FakeVerb:
    value = "no-such-op"


def _parse_index_bullets(content: str) -> list[str]:
    """Return the ordered list of relative paths from `- \\`rel_path\\`` Index bullets."""
    return re.findall(r"^- `(.+)`$", content, re.MULTILINE)


def _parse_body_headings(content: str) -> list[str]:
    """Return the ordered list of relative paths from `## rel_path` body headings.

    The ``## Index`` header is excluded since it is the index section marker,
    not a per-file body heading.
    """
    headings = re.findall(r"^## (.+)$", content, re.MULTILINE)
    return [h for h in headings if h != "Index"]


def test_unknown_handler_raises_keyerror() -> None:
    agent = SkillsStorageAgent()
    try:
        agent._handler_for(_FakeVerb())
    except KeyError:
        return
    raise AssertionError("expected KeyError for unknown storage verb")


# ── Storage capability unit tests ───────────────────────────────────────


def test_storage_single_aggregate_contract() -> None:
    """UT-STORAGE-001: only contract_storage_aggregate defines ISkillsStorageAggregate."""
    assert ISkillsStorageAggregate is not None


def test_exporter_exports_skill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UT-STORAGE-002: SkillsExporter exports skill files into a single Markdown file."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-category" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# My Skill\nSome description\n", encoding="utf-8"
    )

    ref_dir = skill_dir / "references"
    ref_dir.mkdir()
    (ref_dir / "step-1.md").write_text("# Step 1\nStep 1 details\n", encoding="utf-8")

    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "helper.py").write_text("print('test')\n", encoding="utf-8")

    (skill_dir / "README.md").write_text("# Readme content\n", encoding="utf-8")

    exporter = SkillsExporter()
    out_file = exporter.export("my-skill", root=SkillsRoot(pack_root))

    expected = fake_home / ".agents" / "skills" / ".export" / "my-skill.md"
    assert out_file == expected
    assert out_file.is_file()

    content = out_file.read_text(encoding="utf-8")
    assert "## SKILL.md\n\n# My Skill\nSome description" in content
    assert "## references/step-1.md\n\n# Step 1\nStep 1 details" in content
    assert "## scripts/helper.py\n\nprint('test')" in content
    assert "## README.md\n\n# Readme content" in content


def test_exporter_index_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UT-STORAGE-011: Exported Markdown begins with an Index section listing all files.

    Asserts the Index bullets and the per-file ``## <rel_path>`` body sections are in
    lockstep: identical sets and identical ordering, with the Index preceding all
    body sections.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-category" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# My Skill\nSome description\n", encoding="utf-8"
    )

    ref_dir = skill_dir / "references"
    ref_dir.mkdir()
    (ref_dir / "step-1.md").write_text("# Step 1\nStep 1 details\n", encoding="utf-8")
    # Unsupported extension (.dat) should be excluded
    (ref_dir / "cache.dat").write_text("binary-data", encoding="utf-8")

    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "helper.py").write_text("print('test')\n", encoding="utf-8")
    # Unsupported extension (.bin) should be excluded
    (scripts_dir / "data.bin").write_text("binary-data", encoding="utf-8")

    (skill_dir / "README.md").write_text("# Readme content\n", encoding="utf-8")

    exporter = SkillsExporter()
    out_file = exporter.export("my-skill", root=SkillsRoot(pack_root))
    content = out_file.read_text(encoding="utf-8")

    # Index section is the first section
    assert content.startswith("# my-skill\n")
    assert "## Index\n" in content

    index_bullets = _parse_index_bullets(content)
    body_headings = _parse_body_headings(content)

    # Supported files are listed in the Index (and in the body)
    assert set(index_bullets) == {
        "SKILL.md",
        "references/step-1.md",
        "scripts/helper.py",
        "README.md",
    }
    # Unsupported files are NOT in the Index
    assert "cache.dat" not in content
    assert "data.bin" not in content

    # Lockstep invariant: identical set AND identical ordering.
    assert index_bullets == body_headings

    # Index comes before the first file section
    index_pos = content.index("## Index")
    skill_section_pos = content.index("## SKILL.md")
    assert index_pos < skill_section_pos


def test_exporter_skill_md_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UT-STORAGE-013: a SKILL.md-only skill lists exactly ``SKILL.md`` in the Index."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-category" / "only-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Only\n", encoding="utf-8")

    exporter = SkillsExporter()
    out_file = exporter.export("only-skill", root=SkillsRoot(pack_root))
    content = out_file.read_text(encoding="utf-8")

    assert _parse_index_bullets(content) == ["SKILL.md"]
    assert _parse_body_headings(content) == ["SKILL.md"]


def test_exporter_empty_skill_md(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UT-STORAGE-014: an empty SKILL.md still appears as a bullet in the Index."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-category" / "empty-md-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("", encoding="utf-8")

    exporter = SkillsExporter()
    out_file = exporter.export("empty-md-skill", root=SkillsRoot(pack_root))
    content = out_file.read_text(encoding="utf-8")

    # Empty file is still listed in the Index.
    assert _parse_index_bullets(content) == ["SKILL.md"]
    # Body still has the heading (current behavior: bare heading, no body text).
    assert "## SKILL.md" in content


def test_exporter_hidden_files_excluded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UT-STORAGE-015: hidden files/directories are excluded from the Index."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-category" / "hidden-skill"
    skill_dir.mkdir(parents=True)
    # Root-level SKILL.md is required by resolve_skill_dir; a dotted sibling
    # (``.SKILL.md``) is distinct on a case-sensitive filesystem and must be skipped.
    (skill_dir / "SKILL.md").write_text("# Hidden\n", encoding="utf-8")
    (skill_dir / ".SKILL.md").write_text("# dotted skill\n", encoding="utf-8")
    (skill_dir / "README.md").write_text("# Readme\n", encoding="utf-8")
    (skill_dir / ".README.md").write_text("# dotted readme\n", encoding="utf-8")

    ref_dir = skill_dir / "references"
    ref_dir.mkdir()
    (ref_dir / "visible.md").write_text("# Visible\n", encoding="utf-8")
    # Hidden file and hidden directory should both be excluded.
    (ref_dir / ".secret.md").write_text("# secret\n", encoding="utf-8")
    hidden_subdir = ref_dir / ".cache"
    hidden_subdir.mkdir()
    (hidden_subdir / "junk.md").write_text("# junk\n", encoding="utf-8")

    exporter = SkillsExporter()
    out_file = exporter.export("hidden-skill", root=SkillsRoot(pack_root))
    content = out_file.read_text(encoding="utf-8")

    bullets = _parse_index_bullets(content)
    # Root-level supported files survive the hidden-dir filter.
    assert "SKILL.md" in bullets
    assert "README.md" in bullets
    assert "references/visible.md" in bullets
    # Root-level and nested hidden files/dirs are excluded.
    assert not any(".SKILL" in b or ".README" in b for b in bullets)
    assert not any(".secret" in b or ".cache" in b for b in bullets)
    assert ".SKILL.md" not in content
    assert ".README.md" not in content
    assert ".secret.md" not in content
    assert ".cache" not in content


def test_format_index_section_empty() -> None:
    """UT-STORAGE-016: empty file list renders heading + Index header + separator only."""
    exporter = SkillsExporter()
    out = exporter._format_index_section("demo", [])
    assert out == "# demo\n\n## Index\n\n\n---\n"


def test_format_index_section_single() -> None:
    """UT-STORAGE-017: single entry renders exactly one bullet."""
    exporter = SkillsExporter()
    out = exporter._format_index_section("demo", [("SKILL.md", Path("SKILL.md"))])
    assert out == "# demo\n\n## Index\n\n- `SKILL.md`\n\n---\n"


def test_format_index_section_multiple() -> None:
    """UT-STORAGE-018: multiple entries render bullets in the provided order."""
    exporter = SkillsExporter()
    out = exporter._format_index_section(
        "demo",
        [
            ("SKILL.md", Path("SKILL.md")),
            ("references/a.md", Path("references/a.md")),
            ("scripts/run.py", Path("scripts/run.py")),
        ],
    )
    assert out == (
        "# demo\n\n## Index\n\n"
        "- `SKILL.md`\n"
        "- `references/a.md`\n"
        "- `scripts/run.py`\n\n"
        "---\n"
    )


def test_exporter_skill_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UT-STORAGE-003: SkillsExporter raises SkillNotFoundError on missing skill."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    pack_root.mkdir(parents=True)

    exporter = SkillsExporter()
    with pytest.raises(SkillNotFoundError):
        exporter.export("nonexistent", root=SkillsRoot(pack_root))


def test_agent_execute_export(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """UT-STORAGE-004: SkillsStorageAgent routes EXPORT op to exporter."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-cat" / "sample-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Sample\n", encoding="utf-8")

    agent = SkillsStorageAgent(
        exporter=SkillsExporter(),
        default_root=SkillsRoot(pack_root),
    )
    response = agent.execute(
        StorageRequest(verb=StorageVerb.EXPORT, query="sample-skill")
    )
    assert response.ok is True
    assert response.verb == "export"
    expected_path = str(
        fake_home / ".agents" / "skills" / ".export" / "sample-skill.md"
    )
    assert response.message == expected_path

    # Exported file content carries the Index section.
    exported = Path(response.message).read_text(encoding="utf-8")
    assert exported.startswith("# sample-skill\n")
    assert "## Index" in exported


def test_agent_export_missing_skill_name() -> None:
    """UT-STORAGE-005: EXPORT without query returns usage error."""
    agent = SkillsStorageAgent(exporter=SkillsExporter())
    response = agent.execute(StorageRequest(verb=StorageVerb.EXPORT, query=""))
    assert response.ok is False
    assert response.exit_code == EXIT_USAGE
    assert "Skill name required" in response.message


def test_archiver_plan_archive_uses_home_archive_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UT-STORAGE-006: SkillsArchiver plans archive under ~/.agents/skills/.archive/."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-cat" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# My Skill\n", encoding="utf-8")

    archiver = SkillsArchiver()
    plan = archiver.plan_archive("my-skill", root=SkillsRoot(pack_root))

    expected_destination = (
        fake_home / ".agents" / "skills" / ".archive" / "test-cat" / "my-skill"
    )
    assert plan.destination == expected_destination
    assert plan.kind == "archive"


def test_archiver_and_restore_share_same_archive_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UT-STORAGE-007: Archiver archives to and Restore restores from .agents/skills/.archive/."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-cat" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# My Skill\n", encoding="utf-8")

    expected_archived = (
        fake_home / ".agents" / "skills" / ".archive" / "test-cat" / "my-skill"
    )

    archiver = SkillsArchiver()
    restore = SkillsRestore()

    # 1. Archive the skill
    archive_res = archiver.archive("my-skill", root=SkillsRoot(pack_root))
    assert archive_res["archived"] is True
    assert not skill_dir.exists()
    assert (expected_archived / "SKILL.md").exists()

    # 2. Restore the skill
    restore_res = restore.restore("my-skill", root=SkillsRoot(pack_root))
    assert restore_res["restored"] is True
    assert not expected_archived.exists()
    assert (skill_dir / "SKILL.md").exists()


def test_agent_execute_archive_and_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UT-STORAGE-008: SkillsStorageAgent routes ARCHIVE and RESTORE using .agents/skills/.archive/."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-cat" / "round-trip-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Round Trip\n", encoding="utf-8")

    expected_archived = (
        fake_home / ".agents" / "skills" / ".archive" / "test-cat" / "round-trip-skill"
    )

    agent = SkillsStorageAgent(
        archiver=SkillsArchiver(),
        restore=SkillsRestore(),
        default_root=SkillsRoot(pack_root),
    )

    # 1. Execute ARCHIVE
    arc_resp = agent.execute(
        StorageRequest(verb=StorageVerb.ARCHIVE, query="round-trip-skill")
    )
    assert arc_resp.ok is True
    assert arc_resp.verb == "archive"
    assert not skill_dir.exists()
    assert (expected_archived / "SKILL.md").exists()

    # 2. Execute RESTORE
    res_resp = agent.execute(
        StorageRequest(verb=StorageVerb.RESTORE, query="round-trip-skill")
    )
    assert res_resp.ok is True
    assert res_resp.verb == "restore"
    assert not expected_archived.exists()
    assert (skill_dir / "SKILL.md").exists()


def test_agent_archive_missing_skill_name() -> None:
    """UT-STORAGE-009: ARCHIVE without query returns usage error."""
    agent = SkillsStorageAgent(archiver=SkillsArchiver())
    response = agent.execute(StorageRequest(verb=StorageVerb.ARCHIVE, query=""))
    assert response.ok is False
    assert response.exit_code == EXIT_USAGE
    assert "Skill name required" in response.message


def test_agent_restore_missing_skill_name() -> None:
    """UT-STORAGE-010: RESTORE without query returns usage error."""
    agent = SkillsStorageAgent(restore=SkillsRestore())
    response = agent.execute(StorageRequest(verb=StorageVerb.RESTORE, query=""))
    assert response.ok is False
    assert response.exit_code == EXIT_USAGE
    assert "Skill name required" in response.message


def test_exporter_nested_subdirectory_in_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UT-STORAGE-019: deeply nested files appear with their full relative path in the Index."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-category" / "nested-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Nested\n", encoding="utf-8")

    deep_dir = skill_dir / "references" / "sub" / "deep"
    deep_dir.mkdir(parents=True)
    (deep_dir / "file.md").write_text("# Deep file\n", encoding="utf-8")

    exporter = SkillsExporter()
    out_file = exporter.export("nested-skill", root=SkillsRoot(pack_root))
    content = out_file.read_text(encoding="utf-8")

    bullets = _parse_index_bullets(content)
    assert "references/sub/deep/file.md" in bullets
    assert _parse_body_headings(content) == bullets


def test_exporter_per_extension_inclusion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UT-STORAGE-020: every supported extension is included; unsupported ones dropped.

    Creates one file per supported extension (.md, .py, .rs, .ts, .json, .sh, .toml)
    plus one unsupported (.dat), and asserts each supported file appears as an Index
    bullet with its full relative path while the .dat file does not. This pins
    the extension filter so a typo dropping a legitimate extension is caught.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-category" / "ext-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Ext\n", encoding="utf-8")

    ref_dir = skill_dir / "references"
    ref_dir.mkdir()

    supported = {
        ".md": "note.md",
        ".py": "module.py",
        ".rs": "lib.rs",
        ".ts": "index.ts",
        ".json": "data.json",
        ".sh": "run.sh",
        ".toml": "persona.toml",
    }
    expected_paths: list[str] = ["SKILL.md"]
    for ext, name in supported.items():
        if ext == ".toml":
            (ref_dir / name).write_text(f"# {ext} sample\n", encoding="utf-8")
        else:
            (ref_dir / name).write_text(f"// {ext} sample\n", encoding="utf-8")
        expected_paths.append(f"references/{name}")

    # Location-agnostic: a .toml under scripts/ is also included.
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "persona.toml").write_text(
        "# scripts .toml sample\n", encoding="utf-8"
    )
    expected_paths.append("scripts/persona.toml")

    (ref_dir / "binary.dat").write_text("binary-data", encoding="utf-8")

    exporter = SkillsExporter()
    out_file = exporter.export("ext-skill", root=SkillsRoot(pack_root))
    content = out_file.read_text(encoding="utf-8")

    bullets = _parse_index_bullets(content)
    for rel_path in expected_paths:
        assert rel_path in bullets
    # Unsupported extension is not listed.
    assert "references/binary.dat" not in bullets
    assert "binary.dat" not in content

    # .toml body content flows through the export.
    assert "## references/persona.toml\n\n# .toml sample" in content

    # Each supported file also has a matching body section, in lockstep.
    assert _parse_body_headings(content) == bullets
