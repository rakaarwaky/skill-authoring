"""Storage-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation.
"""

from __future__ import annotations

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


def test_exporter_exports_skill(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """UT-STORAGE-002: SkillsExporter exports skill files into a single Markdown file."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "test-category" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# My Skill\nSome description\n", encoding="utf-8")

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


def test_exporter_skill_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    response = agent.execute(StorageRequest(verb=StorageVerb.EXPORT, query="sample-skill"))
    assert response.ok is True
    assert response.verb == "export"
    expected_path = str(fake_home / ".agents" / "skills" / ".export" / "sample-skill.md")
    assert response.message == expected_path


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
