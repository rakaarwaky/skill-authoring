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
from storage.src.capabilities_skills_exporter import SkillsExporter


def test_unknown_verb_raises_keyerror() -> None:
    agent = SkillsStorageAgent()
    try:
        agent._handler_for(StorageVerb.BOOTSTRAP)
    except KeyError:
        return
    raise AssertionError("expected KeyError for unknown storage verb")


# ── Storage capability unit tests ───────────────────────────────────────

def test_storage_single_aggregate_contract() -> None:
    """UT-STORAGE-001: only contract_storage_aggregate defines ISkillsStorageAggregate."""
    assert ISkillsStorageAggregate is not None


def test_exporter_exports_skill(tmp_path: Path) -> None:
    """UT-STORAGE-002: SkillsExporter exports skill files into a single Markdown file."""
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

    assert out_file == pack_root / ".export" / "my-skill.md"
    assert out_file.is_file()

    content = out_file.read_text(encoding="utf-8")
    assert "## SKILL.md\n\n# My Skill\nSome description" in content
    assert "## references/step-1.md\n\n# Step 1\nStep 1 details" in content
    assert "## scripts/helper.py\n\nprint('test')" in content
    assert "## README.md\n\n# Readme content" in content


def test_exporter_skill_not_found(tmp_path: Path) -> None:
    """UT-STORAGE-003: SkillsExporter raises SkillNotFoundError on missing skill."""
    pack_root = tmp_path / "skills"
    pack_root.mkdir(parents=True)

    exporter = SkillsExporter()
    with pytest.raises(SkillNotFoundError):
        exporter.export("nonexistent", root=SkillsRoot(pack_root))


def test_agent_execute_export(tmp_path: Path) -> None:
    """UT-STORAGE-004: SkillsStorageAgent routes EXPORT op to exporter."""
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
    expected_path = str(pack_root / ".export" / "sample-skill.md")
    assert response.message == expected_path


def test_agent_export_missing_skill_name() -> None:
    """UT-STORAGE-005: EXPORT without query returns usage error."""
    agent = SkillsStorageAgent(exporter=SkillsExporter())
    response = agent.execute(StorageRequest(verb=StorageVerb.EXPORT, query=""))
    assert response.ok is False
    assert response.exit_code == EXIT_USAGE
    assert "Skill name required" in response.message
