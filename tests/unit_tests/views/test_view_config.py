"""Unit tests for ASDL view binding config parsing and validation."""

from __future__ import annotations

from pathlib import Path

from asdl.diagnostics import Severity
from asdl.views import load_view_config, parse_view_config_string


def test_parse_view_config_assigns_default_rule_ids() -> None:
    """Parser assigns deterministic default rule IDs and preserves explicit IDs."""
    yaml_content = "\n".join(
        [
            "config_3:",
            "  description: Testbench for swmatrix row",
            "  view_order: [default, behave]",
            "  rules:",
            "    - match: {path: tb.dut, instance: SR_row}",
            "      bind: ShiftReg_row_25@behave",
            "    - id: sr_module_override",
            "      match: {module: swmatrix_Tgate}",
            "      bind: swmatrix_Tgate@behave",
        ]
    )

    config, diagnostics = parse_view_config_string(yaml_content)

    assert diagnostics == []
    assert config is not None
    profile = config.profiles["config_3"]
    assert profile.view_order == ["default", "behave"]
    assert len(profile.rules) == 2
    assert profile.rules[0].id == "rule1"
    assert profile.rules[1].id == "sr_module_override"


def test_parse_view_config_rejects_instance_module_combo() -> None:
    """Parser rejects match entries that set both instance and module predicates."""
    yaml_content = "\n".join(
        [
            "demo:",
            "  view_order: [default]",
            "  rules:",
            "    - match:",
            "        path: tb.dut",
            "        instance: SR_row",
            "        module: ShiftReg_row_25",
            "      bind: ShiftReg_row_25@behave",
        ]
    )

    config, diagnostics = parse_view_config_string(yaml_content)

    assert config is None
    assert diagnostics
    assert diagnostics[0].severity is Severity.ERROR
    assert "instance" in diagnostics[0].message
    assert "module" in diagnostics[0].message


def test_parse_view_config_rejects_empty_view_order() -> None:
    """Parser rejects profiles with empty baseline view precedence."""
    yaml_content = "\n".join(
        [
            "demo:",
            "  view_order: []",
        ]
    )

    config, diagnostics = parse_view_config_string(yaml_content)

    assert config is None
    assert diagnostics
    assert diagnostics[0].severity is Severity.ERROR
    assert "view_order" in diagnostics[0].message


def test_parse_view_config_emits_deterministic_error_order() -> None:
    """Schema diagnostics are returned in deterministic path-sorted order."""
    yaml_content = "\n".join(
        [
            "z_profile:",
            "  view_order: []",
            "a_profile:",
            "  view_order: [default]",
            "  rules:",
            "    - match: {}",
            "      bind: bad@symbol@view",
        ]
    )

    config, diagnostics = parse_view_config_string(yaml_content)

    assert config is None
    assert diagnostics
    assert len(diagnostics) == 3
    assert "a_profile.rules.0.bind" in diagnostics[0].message
    assert "a_profile.rules.0.match" in diagnostics[1].message
    assert "z_profile.view_order" in diagnostics[2].message


def test_load_view_config_returns_parse_diagnostic_for_malformed_yaml(
    tmp_path: Path,
) -> None:
    """File-based loader converts malformed YAML into parser diagnostics."""
    config_path = tmp_path / "view_config.yaml"
    config_path.write_text("profile: [default\n", encoding="utf-8")

    config, diagnostics = load_view_config(config_path)

    assert config is None
    assert diagnostics
    assert diagnostics[0].severity is Severity.ERROR
    assert "Failed to parse view config YAML" in diagnostics[0].message
