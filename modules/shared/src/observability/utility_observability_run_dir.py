"""Run-dir cleanup utilities for observability traces.

Stateless shared utility: clears per-action run-dir artifacts so trace
capabilities (phrase / usage / memory) can clear run-dir artifacts without
cross-capability imports. Owned by observability shared kernel; consumed by
trace capabilities and re-exported by the root container for AES504 wiring.

Does NOT clear .session/ or manifest.json — those are owned by
scan_sessions which clears them itself.
"""

from __future__ import annotations

import os
import shutil

_KNOWN_ACTIONS = frozenset({"phrases", "phrase", "usage", "memory"})


def clear_run_dir(run_dir: str, action: str = "phrases") -> None:
    """Remove existing run-dir artifacts relevant to *action* before a fresh write.

    Clearing ownership:
      - scan_sessions owns .session/ and manifest.json — it clears those itself
        before writing session records; phrase/usage capabilities never touch them.
      - phrase capability clears only phrase.json.
      - usage capability clears only usage.json.
      - memory capability clears only memory.json.

    targets:
      phrases -> phrase.json  (.session/, manifest.json owned by scan_sessions)
      phrase  -> phrase.json   (.session/, manifest.json owned by scan_sessions)
      usage   -> usage.json     (.session/, manifest.json owned by scan_sessions)
      memory  -> memory.json
    """
    if not run_dir:
        return
    run_dir = os.path.abspath(run_dir)
    if not os.path.isdir(run_dir):
        return

    targets = {
        "phrases": ("phrase.json",),
        "phrase": ("phrase.json",),
        "usage": ("usage.json",),
        "memory": ("memory.json",),
    }.get(action)
    if targets is None:
        raise ValueError(
            f"Unknown action {action!r} for clear_run_dir; "
            f"expected one of: {', '.join(sorted(_KNOWN_ACTIONS))}"
        )

    for entry in targets:
        path = os.path.join(run_dir, entry)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise OSError(
                f"Failed to clear artifact {path!r} while cleaning run_dir "
                f"{run_dir!r} (action={action!r}): {exc}. "
                "Check file permissions or whether the file is locked/in use."
            ) from exc


__all__ = [
    "clear_run_dir",
]
