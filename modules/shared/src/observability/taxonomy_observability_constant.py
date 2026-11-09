"""Observability-domain constants (AES taxonomy layer).

Constants consumed by trace scan / phrase mining capabilities:
session root, rollup limits, and phrase thresholds.

Pure literals only — no functions, no I/O.
"""

from __future__ import annotations

from typing import Final

#: Root env var naming the Grok home where session traces live.
GROK_HOME_ENV: Final = "GROK_HOME"

#: Minimum distinct sessions a phrase must appear in to be reported.
MIN_SESSIONS_DEFAULT: Final = 2

#: Minimum turns for a session to be included in the scan.
MIN_TURNS_DEFAULT: Final = 1

__all__ = [
    "GROK_HOME_ENV",
    "MIN_SESSIONS_DEFAULT",
    "MIN_TURNS_DEFAULT",
]

_layer_symbols = {
    "GROK_HOME_ENV": GROK_HOME_ENV,
    "MIN_SESSIONS_DEFAULT": MIN_SESSIONS_DEFAULT,
    "MIN_TURNS_DEFAULT": MIN_TURNS_DEFAULT,
}
