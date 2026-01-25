import pytest

pytest.importorskip("xdsl")

from xdsl.dialects.builtin import DictionaryAttr, FileLineColLoc, IntAttr, StringAttr
from xdsl.utils.exceptions import VerifyException

from asdl.ir.graphir import (
    EndpointOp,
    GraphPatternOriginAttr,
    InstanceOp,
    ModuleOp,
    NetOp,
    ProgramOp,
)
from asdl.ir.pipeline import verify_graphir_program


def _make_instance(
    *,
    inst_id: str,
    name: str,
    module_id: str = "m1",
    module_kind: str = "module",
) -> InstanceOp:
    return InstanceOp(
        inst_id=inst_id,
        name=name,
        module_ref=(module_kind, module_id),
        module_ref_raw=module_id,
    )


def _make_src_annotations(file: str, line: int, col: int) -> DictionaryAttr:
    return DictionaryAttr(
        {"src": FileLineColLoc(StringAttr(file), IntAttr(line), IntAttr(col))}
    )


def _make_endpoint(
    *,
    endpoint_id: str,
    inst_id: str,
    port_path: str,
    annotations: DictionaryAttr | None = None,
) -> EndpointOp:
    return EndpointOp(
        endpoint_id=endpoint_id,
        inst_id=inst_id,
        port_path=port_path,
        annotations=annotations,
    )


def _make_net(*, net_id: str, name: str, endpoints: list[EndpointOp]) -> NetOp:
    return NetOp(net_id=net_id, name=name, region=endpoints)


def test_module_rejects_duplicate_net_names() -> None:
    net_a = _make_net(net_id="n1", name="N", endpoints=[])
    net_b = _make_net(net_id="n2", name="N", endpoints=[])
    module = ModuleOp(module_id="m1", name="top", file_id="a.asdl", region=[net_a, net_b])

    with pytest.raises(VerifyException):
        module.verify()


def test_module_rejects_duplicate_instance_names() -> None:
    inst_a = _make_instance(inst_id="i1", name="U1")
    inst_b = _make_instance(inst_id="i2", name="U1")
    module = ModuleOp(module_id="m1", name="top", file_id="a.asdl", region=[inst_a, inst_b])

    with pytest.raises(VerifyException):
        module.verify()


def test_module_rejects_endpoint_at_module_level() -> None:
    endpoint = _make_endpoint(endpoint_id="e1", inst_id="i1", port_path="A")
    module = ModuleOp(module_id="m1", name="top", file_id="a.asdl", region=[endpoint])

    with pytest.raises(VerifyException):
        module.verify()


def test_module_rejects_endpoint_missing_instance() -> None:
    endpoint = _make_endpoint(endpoint_id="e1", inst_id="i_missing", port_path="A")
    net = _make_net(net_id="n1", name="net", endpoints=[endpoint])
    module = ModuleOp(module_id="m1", name="top", file_id="a.asdl", region=[net])

    with pytest.raises(VerifyException):
        module.verify()


def test_module_rejects_duplicate_endpoint_inst_port() -> None:
    inst = _make_instance(inst_id="i1", name="U1")
    endpoint_a = _make_endpoint(endpoint_id="e1", inst_id="i1", port_path="A")
    endpoint_b = _make_endpoint(endpoint_id="e2", inst_id="i1", port_path="A")
    net_a = _make_net(net_id="n1", name="net_a", endpoints=[endpoint_a])
    net_b = _make_net(net_id="n2", name="net_b", endpoints=[endpoint_b])
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        region=[inst, net_a, net_b],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_graphir_duplicate_endpoint_diagnostic_uses_instance_name_and_span() -> None:
    inst = _make_instance(inst_id="i1", name="U1")
    endpoint_a = _make_endpoint(endpoint_id="e1", inst_id="i1", port_path="A")
    endpoint_b = _make_endpoint(
        endpoint_id="e2",
        inst_id="i1",
        port_path="A",
        annotations=_make_src_annotations("a.asdl", 3, 5),
    )
    net_a = _make_net(net_id="n1", name="net_a", endpoints=[endpoint_a])
    net_b = _make_net(net_id="n2", name="net_b", endpoints=[endpoint_b])
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        region=[inst, net_a, net_b],
    )
    program = ProgramOp(region=[module])

    diagnostics = verify_graphir_program(program)

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert "U1" in diagnostic.message
    assert "i1" not in diagnostic.message
    assert diagnostic.primary_span is not None
    assert diagnostic.primary_span.file == "a.asdl"
    assert diagnostic.primary_span.start.line == 3
    assert diagnostic.primary_span.start.col == 5


def test_module_accepts_valid_graph() -> None:
    inst_a = _make_instance(inst_id="i1", name="U1")
    inst_b = _make_instance(inst_id="i2", name="U2")
    endpoint_a = _make_endpoint(endpoint_id="e1", inst_id="i1", port_path="A")
    endpoint_b = _make_endpoint(endpoint_id="e2", inst_id="i2", port_path="A")
    net_a = _make_net(net_id="n1", name="net_a", endpoints=[endpoint_a])
    net_b = _make_net(net_id="n2", name="net_b", endpoints=[endpoint_b])
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        region=[inst_a, inst_b, net_a, net_b],
    )

    module.verify()


def test_module_accepts_pattern_expression_table() -> None:
    table = DictionaryAttr(
        {
            "expr1": DictionaryAttr(
                {
                    "expression": StringAttr("N<1|2>"),
                    "kind": StringAttr("net"),
                }
            )
        }
    )
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        region=[],
        pattern_expression_table=table,
    )

    module.verify()
    assert module.attrs is not None
    assert module.attrs.data["pattern_expression_table"] == table


def test_module_rejects_invalid_pattern_expression_table_type() -> None:
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        region=[],
        attrs=DictionaryAttr({"pattern_expression_table": StringAttr("oops")}),
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_net_accepts_pattern_origin_tuple() -> None:
    net = NetOp(
        net_id="n1",
        name="N1",
        region=[],
        pattern_origin=("expr1", 0, "N", ["1", 2]),
    )

    assert isinstance(net.pattern_origin, GraphPatternOriginAttr)
    assert net.pattern_origin.expression_id.data == "expr1"
    assert net.pattern_origin.segment_index.data == 0
    assert net.pattern_origin.base_name.data == "N"
    assert [part.data for part in net.pattern_origin.pattern_parts.data] == ["1", 2]
