"""Contract tests for modules/governance — capability protocol implementations."""
from __future__ import annotations


def test_piner_protocol_contract_methods_exist():
    """CP-GOVERNANCE-005: the piner protocol declares pin/unpin."""
    from shared.src.governance.contract_governance_protocol import (
        ISkillsPinerProtocol,
    )

    assert hasattr(ISkillsPinerProtocol, "pin")
    assert hasattr(ISkillsPinerProtocol, "unpin")


def test_mover_protocol_contract_methods_exist():
    """CP-GOVERNANCE-006: the mover protocol declares plan_move/apply_move."""
    from shared.src.governance.contract_governance_protocol import (
        ISkillsMoverProtocol,
    )

    assert hasattr(ISkillsMoverProtocol, "plan_move")
    assert hasattr(ISkillsMoverProtocol, "apply_move")
