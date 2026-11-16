"""Storage-domain constants (AES taxonomy layer).

Constants consumed by the skill-pack bootstrap and pack-reader capabilities:
pack layout names, marker filenames, and path keys.

Pure literals only — no functions, no I/O.
"""

from __future__ import annotations

from typing import Final

#: The pack root directory name under the repo.
PACK_DIRNAME: Final = "skills"

#: The metadata file describing the pack.
PACK_MANIFEST_FILENAME: Final = "manifest.json"

#: The sidecar holding per-skill usage state.
USAGE_SIDECAR_FILENAME: Final = ".usage.json"

#: The lock file guarding the usage sidecar.
USAGE_LOCK_FILENAME: Final = ".usage.json.lock"

#: The archive directory name.
ARCHIVE_DIRNAME: Final = ".archive"

#: The relative path to the archive tree under the user's home directory.
ARCHIVE_REL_PATH: Final = ".agents/skills/.archive"

#: Standard skill-pack category directories created at bootstrap.
CATEGORY_DIRS: Final[tuple[str, ...]] = (
    "archive",
    "design",
    "discovery",
    "governance",
    "maintenance",
    "observability",
    "storage",
)

__all__ = [
    "ARCHIVE_DIRNAME",
    "ARCHIVE_REL_PATH",
    "CATEGORY_DIRS",
    "PACK_DIRNAME",
    "PACK_MANIFEST_FILENAME",
    "USAGE_LOCK_FILENAME",
    "USAGE_SIDECAR_FILENAME",
]

_layer_symbols = {
    "ARCHIVE_DIRNAME": ARCHIVE_DIRNAME,
    "ARCHIVE_REL_PATH": ARCHIVE_REL_PATH,
    "CATEGORY_DIRS": CATEGORY_DIRS,
    "PACK_DIRNAME": PACK_DIRNAME,
    "PACK_MANIFEST_FILENAME": PACK_MANIFEST_FILENAME,
    "USAGE_LOCK_FILENAME": USAGE_LOCK_FILENAME,
    "USAGE_SIDECAR_FILENAME": USAGE_SIDECAR_FILENAME,
}
