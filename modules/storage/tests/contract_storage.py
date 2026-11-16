"""Storage-module contract test (AES704).

Verifies that SkillsStorageAgent implements ISkillsStorageAggregate.
"""

from __future__ import annotations

from shared.src.storage.contract_storage_aggregate import (
    ISkillsStorageAggregate,
)
from storage.src.agent_storage_orchestrator import SkillsStorageAgent


def test_agent_implements_protocol() -> None:
    agent = SkillsStorageAgent()
    assert isinstance(agent, ISkillsStorageAggregate)


def test_exporter_implements_protocol() -> None:
    from shared.src.storage.contract_storage_protocol import (
        ISkillsExportProtocol,
    )
    from storage.src.capabilities_skills_exporter import SkillsExporter

    assert issubclass(SkillsExporter, ISkillsExportProtocol)
    assert isinstance(SkillsExporter(), ISkillsExportProtocol)


def test_archiver_implements_protocol() -> None:
    from shared.src.storage.contract_storage_protocol import (
        ISkillsArchiverProtocol,
    )
    from storage.src.capabilities_skills_archiver import SkillsArchiver

    assert issubclass(SkillsArchiver, ISkillsArchiverProtocol)
    assert isinstance(SkillsArchiver(), ISkillsArchiverProtocol)


def test_restore_implements_protocol() -> None:
    from shared.src.storage.contract_storage_protocol import (
        ISkillsRestoreProtocol,
    )
    from storage.src.capabilities_skills_restore import SkillsRestore

    assert issubclass(SkillsRestore, ISkillsRestoreProtocol)
    assert isinstance(SkillsRestore(), ISkillsRestoreProtocol)
