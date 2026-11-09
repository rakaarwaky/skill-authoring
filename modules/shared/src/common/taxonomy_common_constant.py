"""Shared-kernel constants for the skills domain (AES common layer).

Constants consumed by more than one module domain. A module must import
these from here rather than reaching into a sibling domain's taxonomy
module.

``BM25F_SCORE_SCALE`` lives here because both the discovery ranker
(``map_to_legacy_score``) and the design validator depend on it.
"""

from __future__ import annotations

import re
from typing import Final

# ─── Naming budget ─────────────────────────────────────────────────────

#: Naming budget. ``is_valid_skill_name`` consumes these.
NAME_MIN: Final = 2
NAME_MAX: Final = 64
NAME_RE: Final = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")

# ─── Layout invariants ────────────────────────────────────────────────

#: Category description file name.
CATEGORY_DESCRIPTION_FILENAME: Final = "DESCRIPTION.md"

#: Category directories the walker skips.
IGNORED_CATEGORY_DIRS: Final = frozenset(
    {".git", ".hg", ".svn", "__pycache__", "_archive"}
)

# ─── Archive ───────────────────────────────────────────────────────────

#: Archive directory the ``archive`` mutation moves skills into; the
#: walker skips it (it is in ``IGNORED_CATEGORY_DIRS``).
ARCHIVE_DIRNAME: Final = "_archive"

# ─── Discovery / catalog ─────────────────────────────────────────────

#: The catalog file name (tracked artifact name).
CATALOG_FILENAME: Final = "catalog.json"

#: The loud drift warning: the catalog failed its drift gate, so the
#: answer comes from a live tree scan. Named repair: ``catalog --check``.
DRIFT_WARNING: Final = (
    "WARNING: catalog drift detected — answering from a live tree scan. "
    "Run `catalog --check` to repair catalog.json."
)

# ─── Discovery scoring ────────────────────────────────────────────────

#: Score scale factor: float BM25F score * scale → int legacy projection.
BM25F_SCORE_SCALE: Final = 100

# ─── DM markers ────────────────────────────────────────────────────────

#: The DM2 asset-container marker file.
ASSETS_MARKER_FILENAME: Final = "ASSETS.md"

#: The DM1 nested-pack marker file.
PACK_MARKER_FILENAME: Final = "pack.toml"

__all__ = [
    "ARCHIVE_DIRNAME",
    "ASSETS_MARKER_FILENAME",
    "BM25F_SCORE_SCALE",
    "CATALOG_FILENAME",
    "CATEGORY_DESCRIPTION_FILENAME",
    "DRIFT_WARNING",
    "IGNORED_CATEGORY_DIRS",
    "NAME_MAX",
    "NAME_MIN",
    "NAME_RE",
    "PACK_MARKER_FILENAME",
]
