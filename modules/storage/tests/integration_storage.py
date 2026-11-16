"""Storage-module integration test (AES704).

Verifies storage capability wiring and lifecycle flow end to end.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from shared.src.storage.taxonomy_storage_request import StorageRequest, StorageVerb
from storage.src.agent_storage_orchestrator import SkillsStorageAgent
from storage.src.root_storage_container import create_storage_feature


def test_storage_agent_coordinates_capabilities() -> None:
    agent = SkillsStorageAgent()
    assert agent is not None


def test_storage_container_archive_and_restore_integration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    pack_root = tmp_path / "skills"
    skill_dir = pack_root / "devops" / "ci-runner"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# CI Runner\n", encoding="utf-8")

    archive_target = (
        fake_home / ".agents" / "skills" / ".archive" / "devops" / "ci-runner"
    )

    storage_aggregate = create_storage_feature(root=pack_root)

    # 1. Archive
    arc_res = storage_aggregate.execute(
        StorageRequest(verb=StorageVerb.ARCHIVE, query="ci-runner")
    )
    assert arc_res.ok is True
    assert not skill_dir.exists()
    assert (archive_target / "SKILL.md").exists()

    # 2. Restore
    res_res = storage_aggregate.execute(
        StorageRequest(verb=StorageVerb.RESTORE, query="ci-runner")
    )
    assert res_res.ok is True
    assert (skill_dir / "SKILL.md").exists()
    assert not archive_target.exists()
