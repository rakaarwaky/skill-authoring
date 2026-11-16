"""Maintenance-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation.
"""

from __future__ import annotations

from maintenance.src.agent_maintenance_orchestrator import (
    SkillsMaintenanceAgent,
)
from shared.src.maintenance.taxonomy_maintenance_request import (
    MaintenanceRequest,
    MaintenanceVerb,
)
from shared.src.maintenance.taxonomy_maintenance_response import (
    MaintenanceResponse,
)
from shared.src.maintenance.utility_skills_mutation import archive_root


def test_unknown_verb_returns_usage_error() -> None:
    agent = SkillsMaintenanceAgent(prune=object(), purge=object())
    result = agent.execute(MaintenanceRequest(verb=MaintenanceVerb("bogus")))
    assert isinstance(result, MaintenanceResponse)
    assert result.ok is False


# ── Maintenance capability unit tests ──────────────────────────────────

def test_prune_report_includes_dry_run_flag() -> None:
    """UT-MAINTENANCE-001: prune report carries the dry_run flag."""
    import tempfile
    from pathlib import Path

    from maintenance.src.capabilities_skills_prune import SkillsPrune

    prune = SkillsPrune()
    with tempfile.TemporaryDirectory() as tmp:
        pack_root = Path(tmp)
        archive_root(pack_root).mkdir(parents=True, exist_ok=True)
        report = prune.prune(root=pack_root, days=1, dry_run=True)
        assert report["dry_run"] is True

    report = prune.prune(root=pack_root, days=1, dry_run=False)
    assert report["dry_run"] is False


def test_purge_propagates_oserror_instead_of_swallowing() -> None:
    """UT-MAINTENANCE-002: purge lets OSError propagate from rmtree."""
    import tempfile
    from pathlib import Path

    from maintenance.src.capabilities_skills_purge import SkillsPurge

    purge = SkillsPurge()
    with tempfile.TemporaryDirectory() as tmp:
        pack_root = Path(tmp)
        archived = archive_root(pack_root) / "testcat" / "stale-skill"
        archived.mkdir(parents=True, exist_ok=True)
        (archived / "SKILL.md").write_text("---\nname: stale-skill\n---\n", encoding="utf-8")
        # Make the parent directory read-only so rmtree cannot unlink the directory.
        archived.parent.chmod(0o555)
        try:
            purge.purge(skill="stale-skill", root=pack_root, dry_run=False)
        except OSError:
            return
        finally:
            archived.parent.chmod(0o755)
            import shutil
            shutil.rmtree(archive_root(pack_root) / "testcat", ignore_errors=True)
    raise AssertionError("expected OSError from rmtree without ignore_errors=True")
