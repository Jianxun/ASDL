import textwrap

import pytest

pytest.importorskip("xdsl")

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, ModuleDecl
from asdl.ir import convert_document, convert_graphir_to_ifir, dump_graphir, dump_ifir

EXPECTED_GRAPHIR = textwrap.dedent(
    """\
    graphir.program {
      graphir.module {
        graphir.net {
          graphir.endpoint {endpoint_id = #graphir.graph_id<"e1">, inst_id = #graphir.graph_id<"i1">, port_path = "P"}
        } {net_id = #graphir.graph_id<"n1">, name = "OUT"}
        graphir.net {
          graphir.endpoint {endpoint_id = #graphir.graph_id<"e2">, inst_id = #graphir.graph_id<"i1">, port_path = "N"}
        } {net_id = #graphir.graph_id<"n2">, name = "VSS"}
        graphir.instance {inst_id = #graphir.graph_id<"i1">, name = "R1", module_ref = #graphir.symbol_ref<"device", #graphir.graph_id<"d1">>, module_ref_raw = "res", props = {a = "1", b = "2"}}
      } {module_id = #graphir.graph_id<"m1">, name = "top", file_id = "<string>"}
      graphir.device {
        asdl_ifir.backend {name = "ngspice", template = "R{inst} {ports}"}
      } {device_id = #graphir.graph_id<"d1">, name = "res", file_id = "<string>", ports = ["P", "N"]}
    } {entry = #graphir.graph_id<"m1">}
    """
)

EXPECTED_IFIR = textwrap.dedent(
    """\
    asdl_ifir.design {
      asdl_ifir.module {
        asdl_ifir.net {name = "OUT"}
        asdl_ifir.net {name = "VSS"}
        asdl_ifir.instance {name = "R1", ref = @res, conns = [#asdl_ifir.conn<"P", "OUT">, #asdl_ifir.conn<"N", "VSS">], ref_file_id = "<string>", params = {a = "1", b = "2"}}
      } {sym_name = "top", port_order = [], file_id = "<string>"}
      asdl_ifir.device {
        asdl_ifir.backend {name = "ngspice", template = "R{inst} {ports}"}
      } {sym_name = "res", ports = ["P", "N"], file_id = "<string>"}
    } {top = "top", entry_file_id = "<string>"}
    """
)


def _build_document() -> AsdlDocument:
    return AsdlDocument(
        top="top",
        modules={
            "top": ModuleDecl(
                instances={"R1": "res a=1 b=2"},
                nets={"OUT": ["R1.P"], "VSS": ["R1.N"]},
            )
        },
        devices={
            "res": DeviceDecl(
                ports=["P", "N"],
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")},
            )
        },
    )


def test_dump_graphir_program() -> None:
    program, diagnostics = convert_document(_build_document())

    assert diagnostics == []
    assert program is not None
    assert dump_graphir(program) == EXPECTED_GRAPHIR


def test_dump_ifir_design() -> None:
    program, diagnostics = convert_document(_build_document())

    assert diagnostics == []
    assert program is not None

    design, diagnostics = convert_graphir_to_ifir(program)

    assert diagnostics == []
    assert design is not None
    assert dump_ifir(design) == EXPECTED_IFIR
