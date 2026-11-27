"""Maintenance-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation, the
merged prune capability (archive idle + purge old archives), and the
folded-in usage capability (scan_sessions, write_usage, fold, seed,
reanchor, curated_report, record_use).
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from maintenance.src.agent_maintenance_orchestrator import (
    SkillsMaintenanceAgent,
)
from maintenance.src.capabilities_skills_prune import SkillsPrune
from maintenance.src.capabilties_skills_usage import SkillsObservabilityUsage
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


def test_excluded_paths_includes_session() -> None:
    """UT-MAINTENANCE-002: .session is excluded from pack lifecycle walks."""
    from shared.src.maintenance.utility_lifecycle_support import EXCLUDED_PATHS

    assert ".session" in EXCLUDED_PATHS


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


# ── Usage capability unit tests (ported from observability) ──────────────


def test_write_usage_writes_usage_json(tmp_path) -> None:
    """UT-OBS-013: SkillsObservabilityUsage.write_usage writes usage.json to run_dir."""
    from shared.src.observability.taxonomy_observability_entity import (
        TraceSessionRecord,
    )

    usage = SkillsObservabilityUsage()
    run_dir = str(tmp_path / "usage-run")
    Path(run_dir).mkdir(parents=True, exist_ok=True)

    records: tuple[TraceSessionRecord, ...] = ()
    usage.write_usage("$HOME/.grok", run_dir, records)

    assert (Path(run_dir) / "usage.json").is_file()
    data = json.loads((Path(run_dir) / "usage.json").read_text())
    assert "items" in data
    assert "kept_sessions" in data


def test_scan_sessions_writes_session_records(tmp_path) -> None:
    """UT-MAINT-005: usage's own scan_sessions writes .session/ + manifest.json + usage.json."""
    from shared.src.observability.taxonomy_observability_entity import ScanResult

    usage = SkillsObservabilityUsage()
    run_dir = str(tmp_path / "run")
    Path(run_dir).mkdir(parents=True, exist_ok=True)

    # Empty grok_home — no sessions, but scan_sessions should still work.
    scan_result = usage.scan_sessions(str(tmp_path / "grok"), run_dir)

    assert isinstance(scan_result, ScanResult)
    assert scan_result.sessions_seen == 0
    assert len(scan_result.records) == 0
    assert (Path(run_dir) / "manifest.json").is_file()
    assert (Path(run_dir) / ".session").is_dir()

    # No phrase.json or memory.json involvement.
    assert not (Path(run_dir) / "phrase.json").exists()
    assert not (Path(run_dir) / "memory.json").exists()

    # write_usage after scan_sessions.
    usage.write_usage("$HOME/.grok", run_dir, scan_result.records)
    assert (Path(run_dir) / "usage.json").is_file()


def test_scan_sessions_usage_action_writes_usage_not_phrases(tmp_path) -> None:
    """UT-OBS-009: usage's own scan_sessions + write_usage writes usage.json, not phrase.json."""
    from shared.src.observability.taxonomy_observability_entity import ScanResult

    usage = SkillsObservabilityUsage()
    run_dir = str(tmp_path / "run")
    Path(run_dir).mkdir(parents=True, exist_ok=True)

    scan_result = usage.scan_sessions(str(tmp_path / "grok"), run_dir)
    usage.write_usage("$HOME/.grok", run_dir, scan_result.records)

    assert (Path(run_dir) / "usage.json").is_file()
    assert not (Path(run_dir) / "phrase.json").exists()


def test_fold_used_count_into_sidecar_seeds_analytics(tmp_path, monkeypatch) -> None:
    """UT-OBS-008: SkillsObservabilityUsage.fold_used_count_into_usage writes sessions/last_used/via fields."""
    sidecar = tmp_path / "usage.json"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(json.dumps({
        "items": [
            {
                "name": "my-skill",
                "state": "active",
                "pinned": False,
            }
        ]
    }))
    monkeypatch.setattr(
        "maintenance.src.capabilties_skills_usage.pack_usage_path",
        lambda pack_root=None: sidecar,
    )
    usage_dir = tmp_path / "run"
    usage_dir.mkdir()
    (usage_dir / "usage.json").write_text(json.dumps({
        "items": [
            {
                "kind": "skill",
                "name": "my-skill",
                "used_count": 5,
                "sessions": ["s1", "s2"],
                "last_used": "2026-11-20T10:00:00+00:00",
                "via": {"skill_file_read": 3, "slash": 2},
            }
        ]
    }))

    usage = SkillsObservabilityUsage()
    usage.fold_used_count_into_usage(str(tmp_path), str(usage_dir), ())

    written = json.loads(sidecar.read_text())
    rec = next(i for i in written["items"] if i["name"] == "my-skill")
    assert rec["used_count"] == 5
    assert rec["sessions"] == ["s1", "s2"]
    assert rec["last_used"] == "2026-11-20T10:00:00+00:00"
    assert rec["via"] == {"skill_file_read": 3, "slash": 2}
    # Lifecycle fields preserved.
    assert rec["state"] == "active"
    assert rec["pinned"] is False


def test_seed_record_if_missing_creates_baseline(tmp_path, monkeypatch) -> None:
    """UT-OBS-018: seed_record_if_missing creates a baseline record if skill not present."""
    sidecar = tmp_path / "usage.json"
    sidecar.write_text(json.dumps({"items": [{"name": "existing-skill", "state": "active"}]}))
    monkeypatch.setattr(
        "maintenance.src.capabilties_skills_usage.pack_usage_path",
        lambda pack_root=None: sidecar,
    )

    usage = SkillsObservabilityUsage()
    usage.seed_record_if_missing("new-skill", str(tmp_path))

    data = json.loads(sidecar.read_text())
    new_rec = next(i for i in data["items"] if i["name"] == "new-skill")
    assert new_rec["state"] == "active"
    assert new_rec["used_count"] == 0
    ex_rec = next(i for i in data["items"] if i["name"] == "existing-skill")
    assert ex_rec == {"name": "existing-skill", "state": "active"}

    # Calling again does not overwrite existing record
    new_rec["used_count"] = 42
    sidecar.write_text(json.dumps(data))
    usage.seed_record_if_missing("new-skill", str(tmp_path))
    data2 = json.loads(sidecar.read_text())
    new_rec2 = next(i for i in data2["items"] if i["name"] == "new-skill")
    assert new_rec2["used_count"] == 42


def test_reanchor_clock_updates_timestamps(tmp_path, monkeypatch) -> None:
    """UT-OBS-019: reanchor_clock updates last_activity_at and activity_window_start."""
    sidecar = tmp_path / "usage.json"
    sidecar.write_text(json.dumps({
        "items": [
            {
                "name": "my-skill",
                "state": "active",
                "last_activity_at": "2026-01-01T00:00:00+00:00",
                "activity_window_start": "2026-01-01T00:00:00+00:00",
            }
        ]
    }))
    monkeypatch.setattr(
        "maintenance.src.capabilties_skills_usage.pack_usage_path",
        lambda pack_root=None: sidecar,
    )

    usage = SkillsObservabilityUsage()
    usage.reanchor_clock("my-skill", str(tmp_path))

    data = json.loads(sidecar.read_text())
    rec = next(i for i in data["items"] if i["name"] == "my-skill")
    assert rec["last_activity_at"] > "2026-01-01T00:00:00+00:00"
    assert rec["activity_window_start"] > "2026-01-01T00:00:00+00:00"


def test_curated_report_returns_rows(tmp_path, monkeypatch) -> None:
    """UT-OBS-020: curated_report returns sorted TelemetryRow objects for pack skills."""
    skill_a_dir = tmp_path / "general" / "skill-a"
    skill_a_dir.mkdir(parents=True)
    (skill_a_dir / "SKILL.md").write_text("---\nname: skill-a\n---\n")

    skill_b_dir = tmp_path / "general" / "skill-b"
    skill_b_dir.mkdir(parents=True)
    (skill_b_dir / "SKILL.md").write_text("---\nname: skill-b\n---\n")

    sidecar = tmp_path / "usage.json"
    sidecar.write_text(json.dumps({
        "items": [
            {
                "name": "skill-a",
                "state": "active",
                "pinned": True,
                "used_count": 10,
            }
        ]
    }))
    monkeypatch.setattr(
        "maintenance.src.capabilties_skills_usage.pack_usage_path",
        lambda pack_root=None: sidecar,
    )

    usage = SkillsObservabilityUsage()
    rows = usage.curated_report(str(tmp_path))

    assert len(rows) == 2
    row_a = next(r for r in rows if r.name == "skill-a")
    row_b = next(r for r in rows if r.name == "skill-b")
    assert row_a.name == "skill-a"
    assert row_a.pinned is True
    assert row_a.used_count == 10
    assert row_b.name == "skill-b"
    assert row_b.pinned is False
    assert row_b.used_count == 0


def test_record_use_bumps_used_count(tmp_path, monkeypatch) -> None:
    """UT-OBS-021: record_use increments used_count in usage.json."""
    sidecar = tmp_path / "usage.json"
    sidecar.write_text(json.dumps({
        "items": [
            {
                "name": "my-skill",
                "state": "active",
                "used_count": 3,
            }
        ]
    }))
    monkeypatch.setattr(
        "maintenance.src.capabilties_skills_usage.pack_usage_path",
        lambda pack_root=None: sidecar,
    )

    usage = SkillsObservabilityUsage()
    usage.record_use("my-skill", str(tmp_path))

    data = json.loads(sidecar.read_text())
    rec = next(i for i in data["items"] if i["name"] == "my-skill")
    assert rec["used_count"] == 4
    assert rec["last_activity_at"] is not None
    assert rec["state"] == "active"
    assert rec["pinned"] is False


def test_baseline_record_defaults() -> None:
    """UT-OBS-010: _baseline_record() returns the canonical default fields."""
    from shared.src.maintenance.utility_lifecycle_support import _baseline_record

    rec = _baseline_record()
    assert rec["state"] == "active"
    assert rec["pinned"] is False
    assert isinstance(rec["created_by"], str) and rec["created_by"]
    assert isinstance(rec["created_at"], str) and rec["created_at"]
    assert rec["first_seen_at"] == rec["created_at"]
    assert rec["last_activity_at"] == rec["created_at"]
    assert rec["archived_at"] == ""
    assert rec["used_count"] == 0
    assert isinstance(rec["activity_window_start"], str) and rec["activity_window_start"]
    assert rec["sessions"] == []
    assert rec["last_used"] is None
    assert rec["via"] == {}


def test_normalize_preserves_baseline_defaults() -> None:
    """UT-OBS-011: _normalize() keeps missing fields at baseline defaults."""
    from shared.src.maintenance.utility_lifecycle_support import (
        _baseline_record,
        _normalize,
    )

    baseline = _baseline_record()
    rec = _normalize({"name": "only-name-provided"})
    # All baseline defaults are preserved.
    assert rec["state"] == baseline["state"]
    assert rec["pinned"] == baseline["pinned"]
    assert rec["created_by"] == baseline["created_by"]
    assert rec["used_count"] == baseline["used_count"]
    assert rec["sessions"] == []
    assert rec["last_used"] is None
    assert rec["via"] == {}


def test_agent_usage_handler_routes_to_capability(tmp_path) -> None:
    """UT-MAINT-005: SkillsMaintenanceAgent._execute_usage routes to usage capability."""
    from shared.src.observability.taxonomy_observability_entity import ScanResult

    class FakeUsage:
        def scan_sessions(self, grok_home, run_dir):
            return ScanResult(records=(), sessions_seen=0)

        def write_usage(self, grok_home, run_dir, records):
            return []

        def fold_used_count_into_usage(self, grok_home, run_dir, records):
            pass

        def seed_record_if_missing(self, skill, root):
            pass

        def reanchor_clock(self, skill, root):
            pass

        def curated_report(self, root):
            return ()

        def record_use(self, skill, root):
            pass

    agent = SkillsMaintenanceAgent(usage=FakeUsage())
    run_dir = str(tmp_path / "run")
    result = agent.execute(
        MaintenanceRequest(
            verb="usage",
            flags={"grok_home": "$HOME/.grok", "run_dir": run_dir},
        )
    )
    assert result.ok
    assert result.message.startswith("Usage scanned")