import json
from pathlib import Path

import pytest
import yaml

from click.testing import CliRunner

from asdl.cli import cli

VIEW_FIXTURE_DIR = Path(__file__).parent.parent / "views" / "fixtures"
VIEW_FIXTURE_ASDL = VIEW_FIXTURE_DIR / "view_binding_fixture.asdl"
VIEW_FIXTURE_CONFIG = VIEW_FIXTURE_DIR / "view_binding_fixture.config.yaml"
VIEW_FIXTURE_BINDING = VIEW_FIXTURE_DIR / "view_binding_fixture.config_3.binding.yaml"


def _pipeline_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      U1: leaf",
            "    nets:",
            "      $IN:",
            "        - U1.IN",
            "      $OUT:",
            "        - U1.OUT",
            "  leaf:",
            "    instances:",
            "      R1: res r=2k",
            "    nets:",
            "      $IN:",
            "        - R1.P",
            "      $OUT:",
            "        - R1.N",
            "devices:",
            "  res:",
            "    ports: [P, N]",
            "    parameters:",
            "      r: 1k",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports} {params}\"",
        ]
    )


def _structured_pipeline_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      U1: leaf",
            "    nets:",
            "      $IN:",
            "        - U1.IN",
            "      $OUT:",
            "        - U1.OUT",
            "  leaf:",
            "    instances:",
            "      R1:",
            "        ref: res",
            "        parameters:",
            "          r: 2k",
            "    nets:",
            "      $IN:",
            "        - R1.P",
            "      $OUT:",
            "        - R1.N",
            "devices:",
            "  res:",
            "    ports: [P, N]",
            "    parameters:",
            "      r: 1k",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports} {params}\"",
        ]
    )


def _malformed_structured_pipeline_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      R1:",
            "        ref: res",
            "        params:",
            "          r: 2k",
            "    nets:",
            "      $OUT:",
            "        - R1.P",
            "devices:",
            "  res:",
            "    ports: [P]",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"R{name} {ports}\"",
        ]
    )


def _module_variable_pipeline_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    variables:",
            "      suffix: k",
            "      r_value: 2{suffix}",
            "    instances:",
            "      R1: res r={r_value}",
            "    nets:",
            "      $IN:",
            "        - R1.P",
            "      $OUT:",
            "        - R1.N",
            "devices:",
            "  res:",
            "    ports: [P, N]",
            "    parameters:",
            "      r: 1k",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports} {params}\"",
        ]
    )


def _undefined_variable_pipeline_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    variables:",
            "      known: 2k",
            "    instances:",
            "      R1: res r={missing}",
            "    nets:",
            "      $IN:",
            "        - R1.P",
            "      $OUT:",
            "        - R1.N",
            "devices:",
            "  res:",
            "    ports: [P, N]",
            "    parameters:",
            "      r: 1k",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports} {params}\"",
        ]
    )


def _recursive_variable_pipeline_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    variables:",
            "      a: \"{b}\"",
            "      b: \"{a}\"",
            "    instances:",
            "      R1: res r={a}",
            "    nets:",
            "      $IN:",
            "        - R1.P",
            "      $OUT:",
            "        - R1.N",
            "devices:",
            "  res:",
            "    ports: [P, N]",
            "    parameters:",
            "      r: 1k",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports} {params}\"",
        ]
    )


def _view_config_yaml(view_order: str) -> str:
    return "\n".join(
        [
            "profile_a:",
            f"  view_order: [{view_order}]",
        ]
    )


def _write_import_entry(path: Path, import_path: str) -> None:
    lines = [
        "imports:",
        f"  lib: {import_path}",
        "top: top",
        "modules:",
        "  top:",
        "    instances:",
        "      U1: lib.leaf",
        "    nets:",
        "      $IN:",
        "        - U1.IN",
        "      $OUT:",
        "        - U1.OUT",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_import_entry_without_top(path: Path, import_path: str) -> None:
    lines = [
        "imports:",
        f"  lib: {import_path}",
        "modules:",
        "  top:",
        "    instances:",
        "      U1: lib.leaf",
        "    nets:",
        "      $IN:",
        "        - U1.IN",
        "      $OUT:",
        "        - U1.OUT",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_import_entry_without_top_and_modules(path: Path, import_path: str) -> None:
    lines = [
        "imports:",
        f"  lib: {import_path}",
        "devices:",
        "  cap:",
        "    ports: [P, N]",
        "    backends:",
        "      sim.ngspice:",
        "        template: \"C{name} {ports}\"",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_import_library(path: Path) -> None:
    lines = [
        "top: leaf",
        "modules:",
        "  leaf:",
        "    instances:",
        "      R1: res r=2k",
        "    nets:",
        "      $IN:",
        "        - R1.P",
        "      $OUT:",
        "        - R1.N",
        "devices:",
        "  res:",
        "    ports: [P, N]",
        "    parameters:",
        "      r: 1k",
        "    backends:",
        "      sim.ngspice:",
        "        template: \"{name} {ports} {params}\"",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_import_library_with_view(path: Path) -> None:
    lines = [
        "top: leaf",
        "modules:",
        "  leaf:",
        "    instances:",
        "      R1: res r=2k",
        "    nets:",
        "      $IN:",
        "        - R1.P",
        "      $OUT:",
        "        - R1.N",
        "  leaf@behave:",
        "    instances:",
        "      R2: res r=3k",
        "    nets:",
        "      $IN:",
        "        - R2.P",
        "      $OUT:",
        "        - R2.N",
        "devices:",
        "  res:",
        "    ports: [P, N]",
        "    parameters:",
        "      r: 1k",
        "    backends:",
        "      sim.ngspice:",
        "        template: \"{name} {ports} {params}\"",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _expected_netlist(top_as_subckt: bool) -> str:
    lines = []
    if top_as_subckt:
        lines.append(".subckt top IN OUT")
    lines.append("XU1 IN OUT leaf")
    if top_as_subckt:
        lines.append(".ends top")
    lines.extend(
        [
            ".subckt leaf IN OUT",
            "R1 IN OUT r=2k",
            ".ends leaf",
            ".end",
        ]
    )
    return "\n".join(lines)


def _write_backend_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "backends.yaml"
    config_path.write_text(
        "\n".join(
            [
                "sim.ngspice:",
                '  extension: ".spice"',
                '  comment_prefix: "*"',
                "  templates:",
                '    __subckt_header__: ".subckt {name} {ports}"',
                '    __subckt_footer__: ".ends {name}"',
                '    __subckt_call__: "X{name} {ports} {ref}"',
                '    __netlist_header__: ""',
                '    __netlist_footer__: ".end"',
            ]
        ),
        encoding="utf-8",
    )
    return config_path


@pytest.fixture()
def backend_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    config_path = _write_backend_config(tmp_path)
    monkeypatch.setenv("ASDL_BACKEND_CONFIG", str(config_path))
    return config_path


def test_cli_netlist_default_output(
    tmp_path: Path, backend_config: Path
) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_pipeline_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["netlist", str(input_path)])

    assert result.exit_code == 0
    output_path = tmp_path / "design.spice"
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == _expected_netlist(False)


def test_cli_netlist_top_as_subckt_with_output_flag(
    tmp_path: Path, backend_config: Path
) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_pipeline_yaml(), encoding="utf-8")
    output_path = tmp_path / "custom.spice"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "netlist",
            str(input_path),
            "--backend",
            "sim.ngspice",
            "--top-as-subckt",
            "-o",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == _expected_netlist(True)


def test_cli_netlist_substitutes_module_variables_in_output(
    tmp_path: Path, backend_config: Path
) -> None:
    input_path = tmp_path / "vars.asdl"
    input_path.write_text(_module_variable_pipeline_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["netlist", str(input_path)])

    assert result.exit_code == 0
    output_path = tmp_path / "vars.spice"
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == "R1 IN OUT r=2k\n.end"


def test_cli_netlist_structured_instances_match_inline_output(
    tmp_path: Path, backend_config: Path
) -> None:
    inline_path = tmp_path / "inline.asdl"
    structured_path = tmp_path / "structured.asdl"
    inline_path.write_text(_pipeline_yaml(), encoding="utf-8")
    structured_path.write_text(_structured_pipeline_yaml(), encoding="utf-8")

    runner = CliRunner()
    inline_result = runner.invoke(cli, ["netlist", str(inline_path)])
    structured_result = runner.invoke(cli, ["netlist", str(structured_path)])

    assert inline_result.exit_code == 0
    assert structured_result.exit_code == 0
    inline_output = tmp_path / "inline.spice"
    structured_output = tmp_path / "structured.spice"
    assert inline_output.exists()
    assert structured_output.exists()
    assert structured_output.read_text(encoding="utf-8") == inline_output.read_text(
        encoding="utf-8"
    )


def test_cli_netlist_malformed_structured_instance_reports_parse_diagnostic(
    tmp_path: Path, backend_config: Path
) -> None:
    input_path = tmp_path / "malformed_structured.asdl"
    input_path.write_text(_malformed_structured_pipeline_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["netlist", str(input_path)])

    assert result.exit_code == 1
    stderr = getattr(result, "stderr", "")
    combined = f"{result.output}{stderr}"
    assert "PARSE-003" in combined
    assert "parameters" in combined


def test_cli_netlist_imports_with_lib_root(
    tmp_path: Path,
    backend_config: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    lib_root = tmp_path / "lib"
    lib_root.mkdir()
    lib_file = lib_root / "lib.asdl"
    _write_import_library(lib_file)
    entry_file = tmp_path / "entry.asdl"
    _write_import_entry(entry_file, "lib.asdl")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["netlist", str(entry_file), "--lib", str(lib_root)],
    )

    assert result.exit_code == 0
    output_path = tmp_path / "entry.spice"
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == _expected_netlist(False)


def test_cli_netlist_imports_with_env_fallback(
    tmp_path: Path,
    backend_config: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lib_root = tmp_path / "lib"
    lib_root.mkdir()
    lib_file = lib_root / "lib.asdl"
    _write_import_library(lib_file)
    entry_file = tmp_path / "entry.asdl"
    _write_import_entry(entry_file, "lib.asdl")
    monkeypatch.setenv("ASDL_LIB_PATH", str(lib_root))

    runner = CliRunner()
    result = runner.invoke(cli, ["netlist", str(entry_file)])

    assert result.exit_code == 0
    output_path = tmp_path / "entry.spice"
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == _expected_netlist(False)


def test_cli_netlist_imports_with_qualified_decorated_ref(
    tmp_path: Path,
    backend_config: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    lib_root = tmp_path / "lib"
    lib_root.mkdir()
    lib_file = lib_root / "lib.asdl"
    _write_import_library_with_view(lib_file)
    entry_file = tmp_path / "entry.asdl"
    entry_file.write_text(
        "\n".join(
            [
                "imports:",
                "  lib: lib.asdl",
                "top: top",
                "modules:",
                "  top:",
                "    instances:",
                "      U1: lib.leaf@behave",
                "    nets:",
                "      $IN:",
                "        - U1.IN",
                "      $OUT:",
                "        - U1.OUT",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["netlist", str(entry_file), "--lib", str(lib_root)],
    )

    assert result.exit_code == 0
    output_path = tmp_path / "entry.spice"
    assert output_path.exists()
    output = output_path.read_text(encoding="utf-8")
    assert "XU1 IN OUT leaf_behave" in output
    assert ".subckt leaf_behave IN OUT" in output
    assert "R2 IN OUT r=3k" in output


def test_cli_netlist_imports_without_top_uses_entry_module(
    tmp_path: Path,
    backend_config: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    lib_root = tmp_path / "lib"
    lib_root.mkdir()
    lib_file = lib_root / "lib.asdl"
    _write_import_library(lib_file)
    entry_file = tmp_path / "entry.asdl"
    _write_import_entry_without_top(entry_file, "lib.asdl")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["netlist", str(entry_file), "--lib", str(lib_root)],
    )

    assert result.exit_code == 0
    output_path = tmp_path / "entry.spice"
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == _expected_netlist(False)


def test_cli_netlist_imports_without_top_and_without_entry_modules_errors(
    tmp_path: Path,
    backend_config: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    lib_root = tmp_path / "lib"
    lib_root.mkdir()
    lib_file = lib_root / "lib.asdl"
    _write_import_library(lib_file)
    entry_file = tmp_path / "entry.asdl"
    _write_import_entry_without_top_and_modules(entry_file, "lib.asdl")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["netlist", str(entry_file), "--lib", str(lib_root)],
    )

    assert result.exit_code == 1
    stderr = getattr(result, "stderr", "")
    combined = f"{result.output}{stderr}"
    assert "EMIT-001" in combined


def test_cli_netlist_missing_input_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.asdl"

    runner = CliRunner()
    result = runner.invoke(cli, ["netlist", str(missing_path)])

    assert result.exit_code == 1
    stderr = getattr(result, "stderr", "")
    combined = f"{result.output}{stderr}"
    assert "PARSE-004" in combined


def test_cli_netlist_reports_undefined_module_variable(
    tmp_path: Path, backend_config: Path
) -> None:
    input_path = tmp_path / "undefined_var.asdl"
    input_path.write_text(_undefined_variable_pipeline_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["netlist", str(input_path)])

    assert result.exit_code == 1
    stderr = getattr(result, "stderr", "")
    combined = f"{result.output}{stderr}"
    assert "IR-012" in combined


def test_cli_netlist_reports_recursive_module_variable(
    tmp_path: Path, backend_config: Path
) -> None:
    input_path = tmp_path / "recursive_var.asdl"
    input_path.write_text(_recursive_variable_pipeline_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["netlist", str(input_path)])

    assert result.exit_code == 1
    stderr = getattr(result, "stderr", "")
    combined = f"{result.output}{stderr}"
    assert "IR-013" in combined


def test_cli_netlist_view_fixture_config_profile_writes_binding_sidecar(
    tmp_path: Path, backend_config: Path
) -> None:
    sidecar_path = tmp_path / "bindings.json"
    output_path = tmp_path / "view_fixture_config1.spice"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "netlist",
            str(VIEW_FIXTURE_ASDL),
            "--view-config",
            str(VIEW_FIXTURE_CONFIG),
            "--view-profile",
            "config_1",
            "--binding-sidecar",
            str(sidecar_path),
            "-o",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert sidecar_path.exists()
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    expected = [
        {"path": "tb", "instance": "dut", "resolved": "row"},
        {"path": "tb.dut", "instance": "SR_row", "resolved": "shift_row@behave"},
        {"path": "tb.dut", "instance": "Tgate1", "resolved": "sw_tgate@behave"},
        {"path": "tb.dut", "instance": "Tgate2", "resolved": "sw_tgate@behave"},
        {"path": "tb.dut", "instance": "Tgate_dbg", "resolved": "sw_tgate@behave"},
    ]
    assert [{k: entry[k] for k in ("path", "instance", "resolved")} for entry in payload] == expected
    assert all(entry["rule_id"] is None for entry in payload)


def test_cli_netlist_view_fixture_scoped_override_changes_emitted_refs(
    tmp_path: Path, backend_config: Path
) -> None:
    output_path = tmp_path / "view_fixture_config2.spice"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "netlist",
            str(VIEW_FIXTURE_ASDL),
            "--view-config",
            str(VIEW_FIXTURE_CONFIG),
            "--view-profile",
            "config_2",
            "-o",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    call_refs = [
        line.rsplit(" ", 1)[-1]
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("X")
    ]
    assert "shift_row_behave" in call_refs
    assert "sw_tgate" in call_refs
    assert "sw_tgate_behave" in call_refs


def test_cli_netlist_view_fixture_sidecar_and_mixed_view_emission(
    tmp_path: Path, backend_config: Path
) -> None:
    sidecar_path = tmp_path / "view_fixture_bindings.json"
    output_path = tmp_path / "view_fixture.spice"
    expected = yaml.safe_load(VIEW_FIXTURE_BINDING.read_text(encoding="utf-8"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "netlist",
            str(VIEW_FIXTURE_ASDL),
            "--view-config",
            str(VIEW_FIXTURE_CONFIG),
            "--view-profile",
            "config_3",
            "--binding-sidecar",
            str(sidecar_path),
            "-o",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert sidecar_path.exists()
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert [{k: entry[k] for k in ("path", "instance", "resolved")} for entry in payload] == expected

    assert output_path.exists()
    call_refs = [
        line.rsplit(" ", 1)[-1]
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("X")
    ]
    assert "sw_tgate" in call_refs
    assert "sw_tgate_behave" in call_refs


def test_cli_netlist_view_resolution_failure_exits_nonzero(
    tmp_path: Path, backend_config: Path
) -> None:
    input_path = tmp_path / "view_binding.asdl"
    input_path.write_text(_pipeline_yaml(), encoding="utf-8")
    view_config_path = tmp_path / "view_config.yaml"
    view_config_path.write_text(
        _view_config_yaml("behave"),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "netlist",
            str(input_path),
            "--view-config",
            str(view_config_path),
            "--view-profile",
            "profile_a",
        ],
    )

    assert result.exit_code == 1
    stderr = getattr(result, "stderr", "")
    combined = f"{result.output}{stderr}"
    assert "Unable to resolve baseline view" in combined


def test_cli_netlist_view_fixture_binding_profiles_change_emitted_instance_refs(
    tmp_path: Path, backend_config: Path
) -> None:
    default_output = tmp_path / "profile_default.spice"
    behave_output = tmp_path / "profile_behave.spice"

    runner = CliRunner()
    default_result = runner.invoke(
        cli,
        [
            "netlist",
            str(VIEW_FIXTURE_ASDL),
            "--view-config",
            str(VIEW_FIXTURE_CONFIG),
            "--view-profile",
            "config_2",
            "-o",
            str(default_output),
        ],
    )
    behave_result = runner.invoke(
        cli,
        [
            "netlist",
            str(VIEW_FIXTURE_ASDL),
            "--view-config",
            str(VIEW_FIXTURE_CONFIG),
            "--view-profile",
            "config_1",
            "-o",
            str(behave_output),
        ],
    )

    assert default_result.exit_code == 0
    assert behave_result.exit_code == 0

    default_refs = [
        line.rsplit(" ", 1)[-1]
        for line in default_output.read_text(encoding="utf-8").splitlines()
        if line.startswith("X")
    ]
    behave_refs = [
        line.rsplit(" ", 1)[-1]
        for line in behave_output.read_text(encoding="utf-8").splitlines()
        if line.startswith("X")
    ]
    assert default_refs != behave_refs
    assert "shift_row_behave" in default_refs
    assert "shift_row_behave" in behave_refs
    assert "sw_tgate" in default_refs
    assert "sw_tgate_behave" in behave_refs


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    output = result.output
    assert "Commands:" in output
    assert "netlist" in output
    assert "ir-dump" not in output
    assert "schema" in output
    assert "Generate a netlist from ASDL." in output
    assert "Generate ASDL schema artifacts." in output
