import pytest

pytest.importorskip("xdsl")

from asdl.ast import parse_string
from asdl.emit.ngspice import emit_ngspice
from asdl.ir.pipeline import run_mvp_pipeline


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
            "      ngspice:",
            "        template: \"{name} {ports} {params}\"",
        ]
    )


def test_pipeline_end_to_end_deterministic_top_handling() -> None:
    document, diagnostics = parse_string(_pipeline_yaml())

    assert diagnostics == []
    assert document is not None

    design, pipeline_diags = run_mvp_pipeline(document)
    assert pipeline_diags == []
    assert design is not None

    netlist, emit_diags = emit_ngspice(design)
    assert emit_diags == []
    assert netlist is not None

    design_again, pipeline_diags_again = run_mvp_pipeline(document)
    assert pipeline_diags_again == []
    assert design_again is not None
    netlist_again, emit_diags_again = emit_ngspice(design_again)
    assert emit_diags_again == []
    assert netlist_again == netlist

    lines = netlist.splitlines()
    assert lines[0] == "*.subckt top IN OUT"
    assert lines[1] == "XU1 IN OUT leaf"
    assert lines[2] == "*.ends top"
    assert lines[3] == ".subckt leaf IN OUT"
    assert lines[4] == "R1 IN OUT r=2k"
    assert lines[5] == ".ends leaf"
