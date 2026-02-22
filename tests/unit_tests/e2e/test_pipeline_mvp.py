from pathlib import Path

import pytest

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, ModuleDecl, parse_string
from asdl.diagnostics import Severity
from asdl.emit.netlist import emit_netlist
from asdl.lowering import run_netlist_ir_pipeline

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


def _write_lvs_backend_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "backends_lvs.yaml"
    config_path.write_text(
        "\n".join(
            [
                "lvs.klayout:",
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
            "    parameters:",
            "      r: 1k",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports} {params}\"",
        ]
    )


def _pattern_pipeline_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      \"U<P|N>\": res",
            "    nets:",
            "      \"$OUT<P|N>\":",
            "        - \"U<P|N>.P\"",
            "devices:",
            "  res:",
            "    ports: [P]",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports}\"",
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


def _structured_instance_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      R1:",
            "        ref: res",
            "        parameters:",
            "          r: 2k",
            "    nets:",
            "      N1:",
            "        - R1.P",
            "devices:",
            "  res:",
            "    ports: [P]",
            "    parameters:",
            "      r: 1k",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports} {params}\"",
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
        "    parameters:",
        "      r: 1k",
        "    backends:",
        "      sim.ngspice:",
        "        template: \"{name} {ports} {params}\"",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_pipeline_end_to_end_deterministic_top_handling(
    backend_config: Path,
) -> None:
    document, diagnostics = parse_string(
        _pipeline_yaml(), file_path=Path("entry.asdl")
    )

    assert diagnostics == []
    assert document is not None

    design, pipeline_diags = run_netlist_ir_pipeline(document)
    assert pipeline_diags == []
    assert design is not None
    assert design.entry_file_id is not None
    assert design.entry_file_id == "entry.asdl"

    netlist, emit_diags = emit_netlist(design)
    assert emit_diags == []
    assert netlist is not None

    design_again, pipeline_diags_again = run_netlist_ir_pipeline(document)
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


def test_pipeline_atomizes_patterns_before_emission() -> None:
    document, diagnostics = parse_string(_pattern_pipeline_yaml())

    assert diagnostics == []
    assert document is not None

    design, pipeline_diags = run_netlist_ir_pipeline(document)

    assert pipeline_diags == []
    assert design is not None

    module = next(module for module in design.modules if module.name == "top")
    assert module.ports == ["OUTP", "OUTN"]

    nets = module.nets
    instances = module.instances

    assert [net.name for net in nets] == ["OUTP", "OUTN"]
    assert [inst.name for inst in instances] == ["UP", "UN"]

    assert module.pattern_expression_table is not None
    pattern_table = module.pattern_expression_table
    net_origins = {
        net.name: pattern_table[net.pattern_origin.expression_id].expression
        for net in nets
        if net.pattern_origin is not None
    }
    inst_origins = {
        inst.name: pattern_table[inst.pattern_origin.expression_id].expression
        for inst in instances
        if inst.pattern_origin is not None
    }
    assert net_origins
    assert inst_origins
    assert set(net_origins.values()) == {"OUT<P|N>"}
    assert set(inst_origins.values()) == {"U<P|N>"}

    conns = {
        inst.name: [(conn.port, conn.net) for conn in inst.conns]
        for inst in instances
    }
    assert conns == {"UP": [("P", "OUTP")], "UN": [("P", "OUTN")]}


def test_pipeline_substitutes_module_variables_in_emitted_netlist(
    backend_config: Path,
) -> None:
    document, diagnostics = parse_string(_module_variable_pipeline_yaml())

    assert diagnostics == []
    assert document is not None

    design, pipeline_diags = run_netlist_ir_pipeline(document)
    assert pipeline_diags == []
    assert design is not None

    netlist, emit_diags = emit_netlist(design)
    assert emit_diags == []
    assert netlist is not None

    lines = netlist.splitlines()
    assert lines[0] == "R1 IN OUT r=2k"
    assert lines[1] == ".end"


def test_pipeline_accepts_structured_instance_declarations(
    backend_config: Path,
) -> None:
    document, diagnostics = parse_string(_structured_instance_yaml())

    assert diagnostics == []
    assert document is not None

    design, pipeline_diags = run_netlist_ir_pipeline(document)
    assert pipeline_diags == []
    assert design is not None

    netlist, emit_diags = emit_netlist(design)
    assert emit_diags == []
    assert netlist is not None

    lines = netlist.splitlines()
    assert lines[0] == "R1 N1 r=2k"
    assert lines[1] == ".end"


def test_pipeline_malformed_structured_instance_emits_diagnostic_not_exception() -> None:
    document = AsdlDocument.model_construct(
        modules={
            "top": ModuleDecl.model_construct(
                instances={
                    "R1": {"parameters": {"r": "2k"}},
                },
                nets={"N1": ["R1.P"]},
            )
        },
        devices={
            "res": DeviceDecl(
                ports=["P"],
                parameters={"r": "1k"},
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="R")},
            )
        },
        top="top",
    )

    design, pipeline_diags = run_netlist_ir_pipeline(document)

    assert design is None
    assert any(diag.code == "IR-001" for diag in pipeline_diags)


def test_pipeline_example_swmatrix_substitutes_module_variables_in_emit(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    entry_file = (
        repo_root
        / "examples"
        / "libs"
        / "sw_matrix"
        / "swmatrix_Tgate"
        / "swmatrix_Tgate.asdl"
    )
    pdk_lib_root = repo_root / "examples" / "pdks" / "gf180mcu" / "asdl"

    assert entry_file.exists()
    assert pdk_lib_root.exists()

    design, pipeline_diags = run_netlist_ir_pipeline(
        entry_file=entry_file,
        lib_roots=[pdk_lib_root],
    )
    assert pipeline_diags == []
    assert design is not None

    backend_config_path = _write_lvs_backend_config(tmp_path)
    netlist, emit_diags = emit_netlist(
        design,
        backend_name="lvs.klayout",
        backend_config_path=backend_config_path,
    )
    assert emit_diags == []
    assert netlist is not None

    assert "Mmn T1 gated_control T2 VSSd nfet_03v3 L=0.28u W=1*6*8u" in netlist
    assert "Mmp T1 gated_controlb T2 VDDd pfet_03v3 L=0.28u W=3*6*8u" in netlist


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

    design, pipeline_diags = run_netlist_ir_pipeline(
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

    design, diagnostics = run_netlist_ir_pipeline(entry_file=entry_file)

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

    design, pipeline_diags = run_netlist_ir_pipeline(document)

    assert design is None
    _assert_span_coverage(pipeline_diags)


def test_netlist_diagnostics_have_spans(backend_config: Path) -> None:
    document, diagnostics = parse_string(_missing_conn_yaml())

    assert diagnostics == []
    assert document is not None

    design, pipeline_diags = run_netlist_ir_pipeline(document)

    assert pipeline_diags == []
    assert design is not None

    netlist, emit_diags = emit_netlist(design)

    assert netlist is None
    assert emit_diags
    for diagnostic in emit_diags:
        assert diagnostic.primary_span is None
        assert NO_SPAN_NOTE in (diagnostic.notes or [])
