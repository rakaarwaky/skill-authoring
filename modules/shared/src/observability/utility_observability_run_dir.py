"""Run-dir cleanup utilities for observability traces.

Stateless shared utility: clears per-action run-dir artifacts so trace
capabilities (phrase / usage / memory) can clear run-dir artifacts without
cross-capability imports. Owned by observability shared kernel; consumed by
root-layer containers.

Does NOT clear sessions/ or manifest.json — those are owned by
scan_sessions which clears them itself.
"""

from __future__ import annotations

import os
import shutil


def clear_run_dir(run_dir: str, action: str = "phrases") -> None:
    """Remove existing run-dir artifacts relevant to *action* before a fresh write.

    Clearing ownership:
      - scan_sessions owns sessions/ and manifest.json — it clears those itself
        before writing session records; phrase/usage capabilities never touch them.
      - phrase capability clears only phrase.json.
      - usage capability clears only usage.json.
      - memory capability clears only memory.json.

    targets:
      phrases -> phrase.json   (sessions/, manifest.json owned by scan_sessions)
      usage   -> usage.json    (sessions/, manifest.json owned by scan_sessions)
      memory  -> memory.json
    """
    run_dir = os.path.abspath(run_dir)
    if not os.path.isdir(run_dir):
        return

    targets = {
        "phrases": ("phrases.json",),
        "usage": ("usage.json",),
        "memory": ("memory.json",),
    }.get(action, ())

    for entry in targets:
        path = os.path.join(run_dir, entry)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass


__all__ = [
    "clear_run_dir",
]
