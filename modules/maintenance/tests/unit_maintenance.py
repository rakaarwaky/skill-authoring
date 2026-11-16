"""Maintenance-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation, and the
merged prune capability (archive idle + purge old archives).
"""

from __future__ import annotations

import os
import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from maintenance.src.agent_maintenance_orchestrator import (
    SkillsMaintenanceAgent,
)
from maintenance.src.capabilities_skills_prune import SkillsPrune
from shared.src.maintenance.taxonomy_maintenance_request import (
    MaintenanceRequest,
)
from shared.src.maintenance.taxonomy_maintenance_response import (
    MaintenanceResponse,
)
from shared.src.maintenance.utility_lifecycle_support import write_record
from shared.src.maintenance.utility_skills_mutation import archive_root

# The archive tree is a shared global (~/.agents/skills/.archive); tests must
# clean up their category dirs so cases do not collide on the same slot.
_TEST_CATEGORY = "testcat"


def _cleanup_archive() -> None:
    shutil.rmtree(archive_root(None) / _TEST_CATEGORY, ignore_errors=True)


def test_unknown_verb_returns_usage_error() -> None:
    agent = SkillsMaintenanceAgent(prune=object())
    # Bypass the enum to exercise the agent's unknown-op guard.
    result = agent.execute(MaintenanceRequest(verb="bogus"))  # type: ignore[arg-type]
    assert isinstance(result, MaintenanceResponse)
    assert result.ok is False


# ── Maintenance capability unit tests ──────────────────────────────────

def test_prune_report_includes_dry_run_flag() -> None:
    """UT-MAINTENANCE-001: prune report carries the dry_run flag."""
    prune = SkillsPrune()
    with tempfile.TemporaryDirectory() as tmp:
        pack_root = Path(tmp)
        archive_root(pack_root).mkdir(parents=True, exist_ok=True)
        report = prune.prune(root=pack_root, days=1, dry_run=True)
        assert report.dry_run is True

    report = prune.prune(root=pack_root, days=1, dry_run=False)
    assert report.dry_run is False


def _age_dir(skill_dir: Path, days: int) -> None:
    """Set a skill dir's mtime to *days* ago so purge TTL comparisons fire."""
    old = datetime.now(UTC) - timedelta(days=days)
    old_ts = old.timestamp()
    os.utime(skill_dir, (old_ts, old_ts))
    for child in skill_dir.rglob("*"):
        os.utime(child, (old_ts, old_ts))


def test_prune_archives_idle_and_purges_old_archives() -> None:
    """UT-MAINTENANCE-002: one prune call archives idle skills and purges old archives."""
    _cleanup_archive()
    prune = SkillsPrune()
    with tempfile.TemporaryDirectory() as tmp:
        pack_root = Path(tmp)
        arch_root = archive_root(pack_root)

        # A stale skill that should be archived (last activity 40 days ago).
        stale_dir = pack_root / _TEST_CATEGORY / "stale-skill"
        stale_dir.mkdir(parents=True, exist_ok=True)
        (stale_dir / "SKILL.md").write_text(
            "---\nname: stale-skill\n---\n", encoding="utf-8"
        )
        write_record(
            stale_dir,
            {"state": "active", "last_activity_at": (datetime.now(UTC) - timedelta(days=40)).isoformat()},
            pack_root,
        )

        # An already-archived skill old enough to purge (archived 70 days ago,
        # dir mtime also 70 days ago so max(archived_at, mtime) is old).
        arch_old = arch_root / _TEST_CATEGORY / "old-skill"
        arch_old.mkdir(parents=True, exist_ok=True)
        (arch_old / "SKILL.md").write_text(
            "---\nname: old-skill\n---\n", encoding="utf-8"
        )
        write_record(
            arch_old,
            {"state": "archived", "archived_at": (datetime.now(UTC) - timedelta(days=70)).isoformat()},
            pack_root,
        )
        _age_dir(arch_old, 70)

        try:
            report = prune.prune(root=pack_root, days=30, purge_days=60, dry_run=False)
            assert report.ok is True
            assert report.dry_run is False

            # stale-skill was archived.
            assert (arch_root / _TEST_CATEGORY / "stale-skill").is_dir()
            # old-skill was purged.
            assert not arch_old.exists()
        finally:
            _cleanup_archive()


def test_prune_keeps_freshly_archived() -> None:
    """UT-MAINTENANCE-002b: a freshly archived skill survives the purge pass."""
    _cleanup_archive()
    prune = SkillsPrune()
    with tempfile.TemporaryDirectory() as tmp:
        pack_root = Path(tmp)
        arch_root = archive_root(pack_root)

        stale_dir = pack_root / _TEST_CATEGORY / "stale-skill"
        stale_dir.mkdir(parents=True, exist_ok=True)
        (stale_dir / "SKILL.md").write_text("---\nname: stale-skill\n---\n", encoding="utf-8")
        write_record(
            stale_dir,
            {"state": "active", "last_activity_at": (datetime.now(UTC) - timedelta(days=40)).isoformat()},
            pack_root,
        )

        try:
            # First prune archives stale-skill; second prune must not purge it
            # because it was just archived (mtime is recent).
            prune.prune(root=pack_root, days=30, purge_days=60, dry_run=False)
            assert (arch_root / _TEST_CATEGORY / "stale-skill").is_dir()

            prune.prune(root=pack_root, days=30, purge_days=60, dry_run=False)
            assert (arch_root / _TEST_CATEGORY / "stale-skill").is_dir()
        finally:
            _cleanup_archive()


def test_prune_purge_propagates_oserror() -> None:
    """UT-MAINTENANCE-003: prune lets OSError propagate from rmtree."""
    _cleanup_archive()
    prune = SkillsPrune()
    with tempfile.TemporaryDirectory() as tmp:
        pack_root = Path(tmp)
        arch_root = archive_root(pack_root)
        archived = arch_root / _TEST_CATEGORY / "stale-skill"
        archived.mkdir(parents=True, exist_ok=True)
        (archived / "SKILL.md").write_text("---\nname: stale-skill\n---\n", encoding="utf-8")
        write_record(
            archived,
            {"state": "archived", "archived_at": (datetime.now(UTC) - timedelta(days=70)).isoformat()},
            pack_root,
        )
        _age_dir(archived, 70)

        # Make the parent directory read-only so rmtree cannot unlink the directory.
        archived.parent.chmod(0o555)
        try:
            prune.prune(root=pack_root, days=30, purge_days=60, dry_run=False)
        except OSError:
            return
        finally:
            archived.parent.chmod(0o755)
            _cleanup_archive()
    raise AssertionError("expected OSError from rmtree without ignore_errors=True")