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

#: Exit code for unknown or malformed storage op.
EXIT_USAGE: Final = 2
#: Exit code for issues found during storage op.
EXIT_ISSUES_FOUND: Final = 1

__all__ = [
    "EXIT_ISSUES_FOUND",
    "EXIT_USAGE",
    "PACK_DIRNAME",
    "PACK_MANIFEST_FILENAME",
    "USAGE_LOCK_FILENAME",
    "USAGE_SIDECAR_FILENAME",
]

_layer_symbols = {
    "EXIT_ISSUES_FOUND": EXIT_ISSUES_FOUND,
    "EXIT_USAGE": EXIT_USAGE,
    "PACK_DIRNAME": PACK_DIRNAME,
    "PACK_MANIFEST_FILENAME": PACK_MANIFEST_FILENAME,
    "USAGE_LOCK_FILENAME": USAGE_LOCK_FILENAME,
    "USAGE_SIDECAR_FILENAME": USAGE_SIDECAR_FILENAME,
}
