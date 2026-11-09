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

__all__ = [
    "PACK_DIRNAME",
    "PACK_MANIFEST_FILENAME",
    "USAGE_LOCK_FILENAME",
    "USAGE_SIDECAR_FILENAME",
]

_layer_symbols = {
    "PACK_DIRNAME": PACK_DIRNAME,
    "PACK_MANIFEST_FILENAME": PACK_MANIFEST_FILENAME,
    "USAGE_LOCK_FILENAME": USAGE_LOCK_FILENAME,
    "USAGE_SIDECAR_FILENAME": USAGE_SIDECAR_FILENAME,
}
