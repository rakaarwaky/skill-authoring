"""Unit tests: typed JSON inputSchema on every sac MCP tool descriptor.

Verifies that ``SkillsMcpAdapter.list_tools()`` declares all 19 verbs and
that each descriptor carries a draft-07 ``inputSchema`` with the required
properties, correct types, and enums the CLI accepts.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

_TOOLS_ROOT = Path(__file__).resolve().parents[2]
for _ns in (
    _TOOLS_ROOT,
    _TOOLS_ROOT / "shared" / "src",
    _TOOLS_ROOT / "mcp" / "src",
):
    if _ns.is_dir() and str(_ns) not in sys.path:
        sys.path.insert(0, str(_ns))

from surface_mcp_command import SkillsMcpAdapter

#: Every sac verb the adapter must expose, in registry order.
EXPECTED_TOOLS = (
    "sac_list",
    "sac_read",
    "sac_export",
    "sac_lint",
    "sac_catalog",
    "sac_discover",
    "sac_move",
    "sac_archive",
    "sac_create",
    "sac_status",
    "sac_usage",
    "sac_run",
    "sac_pause",
    "sac_resume",
    "sac_pin",
    "sac_unpin",
    "sac_restore",
    "sac_prune",
    "sac_ledger",
)

#: Tools whose args are mandatory; the schema must list them as required.
REQUIRED_ARGS = {
    "sac_read": ["skill"],
    "sac_export": ["skill"],
    "sac_discover": ["query"],
    "sac_move": ["skill", "target"],
    "sac_archive": ["skill"],
    "sac_create": ["skill", "category"],
    "sac_pin": ["skill"],
    "sac_unpin": ["skill"],
    "sac_restore": ["skill"],
}

#: Property type declarations every schema must honour.
PROPERTY_TYPES = {
    "sac_read": {"skill": "string"},
    "sac_export": {"skill": "string"},
    "sac_lint": {"category": "string"},
    "sac_catalog": {"check": "boolean"},
    "sac_discover": {"query": "string", "limit": "integer"},
    "sac_move": {"skill": "string", "target": "string", "apply": "boolean"},
    "sac_archive": {"skill": "string", "apply": "boolean"},
    "sac_restore": {"skill": "string", "category": "string", "apply": "boolean"},
    "sac_create": {
        "skill": "string",
        "category": "string",
        "kind": "string",
        "description": "string",
        "apply": "boolean",
    },
    "sac_status": {"query": "string"},
    "sac_usage": {"query": "string", "verb": "string"},
    "sac_run": {"apply": "boolean"},
    "sac_pin": {"skill": "string"},
    "sac_unpin": {"skill": "string"},
    "sac_prune": {"days": "integer", "purge_days": "integer", "dry_run": "boolean"},
    "sac_ledger": {"action": "string", "skill": "string"},
}


# ─── Helpers ─────────────────────────────────────────────────────────

def _adapter() -> SkillsMcpAdapter:
    """Build an adapter over a mock aggregate; list_tools never touches it."""
    return SkillsMcpAdapter(MagicMock())


def _descriptors() -> dict:
    """Return descriptors keyed by tool name."""
    return {d["name"]: d for d in _adapter().list_tools()}


def _schema(tool: str) -> dict:
    """Return the inputSchema of one tool, failing loudly when absent."""
    descriptor = _descriptors()[tool]
    assert "inputSchema" in descriptor, f"{tool} descriptor has no inputSchema"
    return descriptor["inputSchema"]


# ─── Tests: registry coverage ────────────────────────────────────────

def test_list_tools_declares_all_nineteen_verbs():
    """UT-MCP-SCHEMA-001: list_tools returns exactly the 19 sac verbs."""
    names = [d["name"] for d in _adapter().list_tools()]

    assert names == list(EXPECTED_TOOLS)
    assert len(names) == 19
    assert len(set(names)) == 19


def test_every_descriptor_carries_an_object_schema():
    """UT-MCP-SCHEMA-002: each descriptor embeds a JSON Schema object."""
    descriptors = _adapter().list_tools()

    assert all("inputSchema" in d for d in descriptors)
    assert all(d["description"] for d in descriptors)
    assert all(d["inputSchema"]["type"] == "object" for d in descriptors)


def test_every_declared_property_is_typed_and_described():
    """UT-MCP-SCHEMA-003: each property declares a type and a description."""
    for descriptor in _adapter().list_tools():
        name = descriptor["name"]
        for prop, spec in descriptor["inputSchema"].get("properties", {}).items():
            assert "type" in spec, f"{name}.{prop} is missing a type"
            assert spec["description"], f"{name}.{prop} is missing a description"


# ─── Tests: required args ────────────────────────────────────────────

def test_required_args_are_declared():
    """UT-MCP-SCHEMA-004: mandatory tool args appear in ``required``."""
    for tool, required in REQUIRED_ARGS.items():
        assert _schema(tool).get("required") == required, tool


def test_create_requires_skill_and_category():
    """UT-MCP-SCHEMA-005: sac_create requires both skill and category."""
    required = _schema("sac_create").get("required")

    assert "skill" in required
    assert "category" in required


def test_tools_without_required_args_omit_the_key():
    """UT-MCP-SCHEMA-006: optional-only tools omit ``required`` entirely."""
    for tool in (
        "sac_list",
        "sac_lint",
        "sac_catalog",
        "sac_status",
        "sac_usage",
        "sac_run",
        "sac_pause",
        "sac_resume",
        "sac_prune",
        "sac_ledger",
    ):
        assert "required" not in _schema(tool), tool


# ─── Tests: property types ───────────────────────────────────────────

def test_property_types_match_cli_arguments():
    """UT-MCP-SCHEMA-007: declared property types match the CLI flags."""
    for tool, props in PROPERTY_TYPES.items():
        schema = _schema(tool)
        assert set(schema["properties"]) == set(props), tool
        for prop, expected in props.items():
            assert schema["properties"][prop]["type"] == expected, f"{tool}.{prop}"


def test_optional_numeric_and_boolean_args_are_typed():
    """UT-MCP-SCHEMA-008: apply/dry_run are boolean, limit/days integer."""
    assert _schema("sac_move")["properties"]["apply"]["type"] == "boolean"
    assert _schema("sac_prune")["properties"]["days"]["type"] == "integer"
    assert _schema("sac_prune")["properties"]["purge_days"]["type"] == "integer"
    assert _schema("sac_prune")["properties"]["dry_run"]["type"] == "boolean"
    assert _schema("sac_discover")["properties"]["limit"]["type"] == "integer"
    assert _schema("sac_discover")["properties"]["limit"]["default"] == 20


# ─── Tests: enums ────────────────────────────────────────────────────

def test_enum_properties_are_constrained():
    """UT-MCP-SCHEMA-009: kind, verb, and ledger action expose their values."""
    assert _schema("sac_create")["properties"]["kind"]["enum"] == ["skill", "category"]
    assert _schema("sac_usage")["properties"]["verb"]["enum"] == [
        "report",
        "seed",
        "reanchor",
    ]


def test_ledger_action_is_a_free_form_string():
    """UT-MCP-SCHEMA-010: ledger action is a string, not a closed enum."""
    action = _schema("sac_ledger")["properties"]["action"]

    assert action["type"] == "string"
    assert "enum" not in action


# ─── Tests: parameterless tools ──────────────────────────────────────

def test_parameterless_tools_declare_empty_properties():
    """UT-MCP-SCHEMA-011: tools with no args declare empty properties."""
    for tool in ("sac_list", "sac_pause", "sac_resume"):
        assert _schema(tool)["properties"] == {}, tool


def test_empty_schemas_are_not_aliased_between_tools():
    """UT-MCP-SCHEMA-012: parameterless tools own distinct schema dicts.

    A shared dict would let a client mutating one tool's schema silently
    alter another tool's advertised arguments.
    """
    adapter = _adapter()
    empty_tools = [
        d["inputSchema"]
        for d in adapter.list_tools()
        if d["inputSchema"].get("properties") == {}
    ]

    assert len(empty_tools) == 3
    assert len({id(schema) for schema in empty_tools}) == 3