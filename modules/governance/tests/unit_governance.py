"""Unit tests for modules/governance — agent routing and capability helpers."""
from __future__ import annotations

from unittest.mock import MagicMock

from shared.src.governance.taxonomy_governance_request import (
    GovernanceRequest,
    GovernanceVerb,
    SkillQuery,
)


def _agent():
    from governance.src.agent_governance_orchestrator import (
        SkillsGovernanceAgent,
    )

    piner = MagicMock()
    mover = MagicMock()
    return SkillsGovernanceAgent(piner=piner, mover=mover), (
        piner,
        mover,
    )


def test_agent_routes_pin_to_piner():
    """UT-GOVERNANCE-001: a PIN request reaches the piner."""
    agent, (piner, _mover) = _agent()
    req = GovernanceRequest(verb=GovernanceVerb.PIN, query=SkillQuery("skill-a"))
    agent.execute(req)
    assert piner.pin.called, "PIN must reach the piner"


def test_agent_routes_unpin_to_piner():
    """UT-GOVERNANCE-002: an UNPIN request reaches the piner."""
    agent, (piner, _mover) = _agent()
    req = GovernanceRequest(verb=GovernanceVerb.UNPIN, query=SkillQuery("skill-a"))
    agent.execute(req)
    assert piner.unpin.called, "UNPIN must reach the piner"


def test_agent_routes_move_to_mover():
    """UT-GOVERNANCE-003: a MOVE request reaches the mover."""
    agent, (_piner, mover) = _agent()
    req = GovernanceRequest(
        verb=GovernanceVerb.MOVE, query=SkillQuery("skill-a"), flags={"target": "cat"}
    )
    agent.execute(req)
    assert mover.plan_move.called, "MOVE must reach the mover"


def test_agent_unknown_op_returns_usage_error():
    """UT-GOVERNANCE-004: an unknown op name returns a usage error."""
    agent, _ = _agent()
    # The op is passed as the raw string name, matching how the surface
    # forwards an unvalidated flag.
    req = GovernanceRequest(verb="bogus-op")
    result = agent.execute(req)
    assert result.ok is False
    assert result.exit_code == 2


def test_agent_missing_capability_raises():
    """UT-GOVERNANCE-005: dispatching to an unwired capability raises."""
    from governance.src.agent_governance_orchestrator import (
        SkillsGovernanceAgent,
    )
    from shared.src.common.taxonomy_common_error import SkillsRootError

    agent = SkillsGovernanceAgent(piner=None, mover=None)
    req = GovernanceRequest(verb=GovernanceVerb.PIN, query=SkillQuery("skill-a"))
    try:
        # Bypass execute()'s SkillsError catch so we can assert the
        # typed raise out of _mutate_skill / _require.
        agent._execute_pin(req, GovernanceVerb.PIN)
    except SkillsRootError:
        return
    raise AssertionError("expected SkillsRootError for an unwired capability")


def test_agent_show_skill_returns_usage_error():
    """UT-GOVERNANCE-006: show_skill returns a usage error, never NotImplementedError."""
    agent, _ = _agent()
    result = agent.show_skill("skill-a")
    assert result.ok is False
    assert result.exit_code == 2
