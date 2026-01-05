from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from asdl.ast import parse_string
from asdl.emit.netlist import emit_netlist
from asdl.ir.pipeline import run_mvp_pipeline


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
