from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from click.testing import CliRunner

from asdl.cli import cli


def _multi_module_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      X1: child",
            "    nets:",
            "      $OUT:",
            "        - X1.IN",
            "  child:",
            "    instances:",
            "      R1: res",
            "    nets:",
            "      $IN:",
            "        - R1.P",
            "devices:",
            "  res:",
            "    ports: [P]",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"R{inst} {ports}\"",
        ]
    )


def _single_module_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      R1: res",
            "    nets:",
            "      $OUT:",
            "        - R1.P",
            "devices:",
            "  res:",
            "    ports: [P]",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"R{inst} {ports}\"",
        ]
    )


def _patterned_visualizer_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      mn_in_<p|n>: nfet",
            "      mn_tail: nfet",
            "      U1: buf",
            "    nets:",
            "      $out:",
            "        - mn_in_<n>.D",
            "      $vss:",
            "        - mn_tail.<S|B>",
            "        - mn_in_<p|n>.B",
            "      $bus:",
            "        - U1.IN<3:1>",
            "devices:",
            "  nfet:",
            "    ports: [D, S, B]",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"M{inst} {ports}\"",
            "  buf:",
            "    ports: [IN]",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"X{inst} {ports}\"",
        ]
    )


def _patterned_net_enum_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      mn_in_<p|n>: nfet",
            "    nets:",
            "      $out_<p|n>:",
            "        - mn_in_<p|n>.D",
            "devices:",
            "  nfet:",
            "    ports: [D]",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"M{inst} {ports}\"",
        ]
    )


def test_cli_visualizer_dump_list_modules(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_multi_module_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["visualizer-dump", str(input_path), "--list-modules"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == 0
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {"top", "child"}


def test_cli_visualizer_dump_module_output(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_single_module_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["visualizer-dump", str(input_path), "--module", "top"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == 0
    assert payload["module"]["name"] == "top"
    assert payload["module"]["ports"] == ["OUT"]
    assert len(payload["instances"]) == 1
    assert payload["instances"][0]["ref_kind"] == "device"
    assert payload["instances"][0]["ref_raw"] == "res"
    assert payload["refs"]["devices"][0]["name"] == "res"


def test_cli_visualizer_dump_expands_literal_enums_and_labels(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_patterned_visualizer_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["visualizer-dump", str(input_path), "--module", "top"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)

    def resolve_expr(expr_id: str) -> str:
        registry = (payload.get("registries") or {}).get("pattern_expressions") or {}
        raw = registry.get(expr_id, {}).get("raw")
        return raw if isinstance(raw, str) and raw else expr_id

    instance_labels = {resolve_expr(inst["name_expr_id"]) for inst in payload["instances"]}
    assert "mn_in_p" in instance_labels
    assert "mn_in_n" in instance_labels
    assert "mn_tail" in instance_labels

    endpoint_labels = {resolve_expr(endpoint["port_expr_id"]) for endpoint in payload["endpoints"]}
    assert "mn_tail.S" in endpoint_labels
    assert "mn_tail.B" in endpoint_labels
    assert "mn_in_n.D" in endpoint_labels

    bus_endpoints = [
        endpoint
        for endpoint in payload["endpoints"]
        if resolve_expr(endpoint["port_expr_id"]) == "U1.IN<3:1>"
    ]
    assert len(bus_endpoints) == 1
    assert bus_endpoints[0].get("conn_label") == "<3>;<2>;<1>"


def test_cli_visualizer_dump_expands_nets_and_remaps_endpoints(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_patterned_net_enum_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["visualizer-dump", str(input_path), "--module", "top"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)

    def resolve_expr(expr_id: str) -> str:
        registry = (payload.get("registries") or {}).get("pattern_expressions") or {}
        raw = registry.get(expr_id, {}).get("raw")
        return raw if isinstance(raw, str) and raw else expr_id

    net_label_by_id = {
        net["net_id"]: resolve_expr(net["name_expr_id"]) for net in payload["nets"]
    }
    assert set(net_label_by_id.values()) == {"out_p", "out_n"}

    endpoint_label_by_id = {
        endpoint["endpoint_id"]: resolve_expr(endpoint["port_expr_id"])
        for endpoint in payload["endpoints"]
    }
    endpoint_net_labels = {
        endpoint_label_by_id[endpoint["endpoint_id"]]: net_label_by_id[endpoint["net_id"]]
        for endpoint in payload["endpoints"]
    }
    assert endpoint_net_labels["mn_in_p.D"] == "out_p"
    assert endpoint_net_labels["mn_in_n.D"] == "out_n"

    for net in payload["nets"]:
        label = resolve_expr(net["name_expr_id"])
        endpoint_labels = {endpoint_label_by_id[endpoint_id] for endpoint_id in net["endpoint_ids"]}
        if label == "out_p":
            assert endpoint_labels == {"mn_in_p.D"}
        elif label == "out_n":
            assert endpoint_labels == {"mn_in_n.D"}
