"""Storage-module benchmark (AES704).

Performance regression benchmark for the storage agent's op dispatch path.
"""

from __future__ import annotations

from storage.src.agent_storage_orchestrator import SkillsStorageAgent


def bench_storage_dispatch() -> None:
    """Time op dispatch through the storage agent."""
    agent = SkillsStorageAgent()
    # Exercise each storage op handler name resolution without capabilities wired.
    for verb in ("archive", "restore", "backup", "rollback"):
        _ = agent._handler_for(verb)
