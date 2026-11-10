"""Maintenance-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation.
"""

from __future__ import annotations

from shared.src.maintenance.taxonomy_maintenance_request import (
    MaintenanceRequest,
    MaintenanceVerb,
)
from shared.src.maintenance.taxonomy_maintenance_response import MaintenanceResponse

from maintenance.src.agent_maintenance_orchestrator import SkillsMaintenanceAgent


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
        (pack_root / "_archive").mkdir()
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
        archived = pack_root / "_archive" / "stale-skill"
        archived.mkdir(parents=True)
        (archived / "SKILL.md").write_text("---\nname: stale-skill\n---\n", encoding="utf-8")
        # Make the directory read-only so rmtree fails.
        archived.chmod(0o000)
        try:
            purge.purge(skill="stale-skill", root=pack_root, dry_run=False)
        except OSError:
            return
        finally:
            archived.chmod(0o755)
    raise AssertionError("expected OSError from rmtree without ignore_errors=True")
