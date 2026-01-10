from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from asdl.ast import parse_string
from asdl.diagnostics import Severity
from asdl.emit.netlist import emit_netlist
from asdl.ir.pipeline import run_mvp_pipeline

NO_SPAN_NOTE = "No source span available."


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
            "    params:",
            "      r: 1k",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports} {params}\"",
        ]
    )


def _invalid_instance_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      U1: leaf badparam",
            "    nets:",
            "      N1:",
            "        - U1.IN",
            "devices:",
            "  leaf:",
            "    ports: [IN]",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports}\"",
        ]
    )


def _missing_conn_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      R1: res",
            "    nets:",
            "      N1:",
            "        - R1.P",
            "devices:",
            "  res:",
            "    ports: [P, N]",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports}\"",
        ]
    )


def _assert_span_coverage(diagnostics) -> None:
    assert diagnostics
    for diagnostic in diagnostics:
        assert diagnostic.primary_span is not None
        if diagnostic.notes:
            assert NO_SPAN_NOTE not in diagnostic.notes


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
        "    params:",
        "      r: 1k",
        "    backends:",
        "      sim.ngspice:",
        "        template: \"{name} {ports} {params}\"",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_pipeline_end_to_end_deterministic_top_handling(
    backend_config: Path,
) -> None:
    document, diagnostics = parse_string(_pipeline_yaml())

    assert diagnostics == []
    assert document is not None

    design, pipeline_diags = run_mvp_pipeline(document)
    assert pipeline_diags == []
    assert design is not None

    netlist, emit_diags = emit_netlist(design)
    assert emit_diags == []
    assert netlist is not None

    design_again, pipeline_diags_again = run_mvp_pipeline(document)
    assert pipeline_diags_again == []
    assert design_again is not None
    netlist_again, emit_diags_again = emit_netlist(design_again)
    assert emit_diags_again == []
    assert netlist_again == netlist

    lines = netlist.splitlines()
    assert lines[0] == "XU1 IN OUT leaf"
    assert lines[1] == ".subckt leaf IN OUT"
    assert lines[2] == "R1 IN OUT r=2k"
    assert lines[3] == ".ends leaf"
    assert lines[4] == ".end"


def test_pipeline_import_graph_success(
    backend_config: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    lib_root = tmp_path / "lib"
    lib_root.mkdir()
    lib_file = lib_root / "lib.asdl"
    _write_import_library(lib_file)
    entry_file = tmp_path / "entry.asdl"
    _write_import_entry(entry_file, "lib.asdl")

    design, pipeline_diags = run_mvp_pipeline(
        entry_file=entry_file,
        lib_roots=[lib_root],
    )

    assert pipeline_diags == []
    assert design is not None

    netlist, emit_diags = emit_netlist(design)
    assert emit_diags == []
    assert netlist is not None

    lines = netlist.splitlines()
    assert lines[0] == "XU1 IN OUT leaf"
    assert lines[1] == ".subckt leaf IN OUT"
    assert lines[2] == "R1 IN OUT r=2k"
    assert lines[3] == ".ends leaf"
    assert lines[4] == ".end"


def test_pipeline_import_graph_missing_import(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    entry_file = tmp_path / "entry.asdl"
    entry_file.write_text(
        "\n".join(
            [
                "imports:",
                "  lib: missing.asdl",
                "modules:",
                "  top: {}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    design, diagnostics = run_mvp_pipeline(entry_file=entry_file)

    assert design is None
    assert any(diag.code == "AST-010" for diag in diagnostics)
    assert any(diag.severity is Severity.ERROR for diag in diagnostics)


def test_parser_diagnostics_have_spans() -> None:
    document, diagnostics = parse_string("- just-a-list\n")

    assert document is None
    _assert_span_coverage(diagnostics)


def test_lowering_diagnostics_have_spans() -> None:
    document, diagnostics = parse_string(_invalid_instance_yaml())

    assert diagnostics == []
    assert document is not None

    design, pipeline_diags = run_mvp_pipeline(document)

    assert design is None
    _assert_span_coverage(pipeline_diags)


def test_netlist_diagnostics_have_spans(backend_config: Path) -> None:
    document, diagnostics = parse_string(_missing_conn_yaml())

    assert diagnostics == []
    assert document is not None

    design, pipeline_diags = run_mvp_pipeline(document)

    assert pipeline_diags == []
    assert design is not None

    netlist, emit_diags = emit_netlist(design)

    assert netlist is None
    _assert_span_coverage(emit_diags)
