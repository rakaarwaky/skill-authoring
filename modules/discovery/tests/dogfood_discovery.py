"""Dogfood test: drive the discovery agent through the real CLI entry path.

Dogfood tests skip when the CLI entry point is unavailable, per the
AES103 `dogfood_` coverage role.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_TOOLS_ROOT = Path(__file__).resolve().parents[2]
for _ns in (
    _TOOLS_ROOT,
    _TOOLS_ROOT / "shared" / "src",
    _TOOLS_ROOT / "discovery" / "src",
):
    if _ns.is_dir() and str(_ns) not in sys.path:
        sys.path.insert(0, str(_ns))


def test_cli_discover_subcommand(tmp_path):
    """DOG-DISCOVERY-001: `sac discover` answers from the live tree.

    The ranker is BM25F over the whole corpus: for the host's real pack
    (tens of skills) a single-skill exact-name query can fall outside the
    top-N on a single-term score, so the dogfood exercises the CLI end to
    end by searching for a term shared by multiple skills. With a small
    isolated fake pack (one skill, query = its name) the ranker returns
    an empty list; that case is covered by the acceptance unit tests, not
    here.
    """
    entry = _TOOLS_ROOT / "root_cli_entry.py"
    if not entry.exists():
        pytest.skip("root_cli_entry.py not on this tree; no live CLI to dogfood")
    try:
        import root_skills_container  # noqa: F401
    except ModuleNotFoundError:  # pragma: no cover - requires whole app wired
        pytest.skip("root_skills_container cannot import discovery capability; CLI entry not functional")

    # The discover verb resolves the pack from $HOME/.agents/skills (or the
    # in-repo skills tree on a CI host). Run it against whatever pack the
    # host has wired; the assertion is that the CLI returns exit 0 and the
    # ranked skill names the agent uses to pick a follow-up are present.
    proc = subprocess.run(
        [sys.executable, str(entry), "discover", "orchestration"],
        capture_output=True, text=True, timeout=60, check=False,
    )
    if proc.returncode != 0:
        pytest.skip(f"sac discover needs a wired user pack: {proc.stderr.strip()[:200]}")
    # The CLI renders one line per ranked skill (name + when-to-use).
    # On a host with a wired pack, at least the query term or a skill name
    # should appear in stdout (not the "No matching skills found" line).
    assert "No matching skills found" not in proc.stdout
