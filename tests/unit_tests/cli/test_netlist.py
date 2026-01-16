from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from click.testing import CliRunner

from asdl.cli import cli


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


def test_cli_netlist_missing_input_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.asdl"

    runner = CliRunner()
    result = runner.invoke(cli, ["netlist", str(missing_path)])

    assert result.exit_code == 1
    stderr = getattr(result, "stderr", "")
    combined = f"{result.output}{stderr}"
    assert "PARSE-004" in combined


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    output = result.output
    assert "Commands:" in output
    assert "netlist" in output
    assert "schema" in output
    assert "Generate a netlist from ASDL." in output
    assert "Generate ASDL schema artifacts." in output
