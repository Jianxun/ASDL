import pytest

pytest.importorskip("xdsl")

from xdsl.utils.exceptions import VerifyException

from asdl.ir.graphir import (
    BundleOp,
    EndpointOp,
    InstanceOp,
    ModuleOp,
    NetOp,
    PatternExprOp,
)


def _make_instance(*, inst_id: str, name: str) -> InstanceOp:
    return InstanceOp(
        inst_id=inst_id,
        name=name,
        module_ref=("module", "m1"),
        module_ref_raw="m1",
    )


def _make_endpoint(*, endpoint_id: str, inst_id: str, port_path: str) -> EndpointOp:
    return EndpointOp(endpoint_id=endpoint_id, inst_id=inst_id, port_path=port_path)


def _make_net(*, net_id: str, name: str, endpoints: list[EndpointOp]) -> NetOp:
    return NetOp(net_id=net_id, name=name, region=endpoints)


def _make_param_ref(*, inst_id: str, name: str) -> tuple[str, str]:
    return (inst_id, name)


def test_pattern_expr_net_owner_requires_net_id() -> None:
    inst = _make_instance(inst_id="i1", name="U1")
    endpoint = _make_endpoint(endpoint_id="e1", inst_id="i1", port_path="A")
    net = _make_net(net_id="n1", name="N", endpoints=[endpoint])
    bundle = BundleOp(
        bundle_id="b1",
        kind="net",
        base_name="N",
        pattern_type="literal",
        members=["n1"],
    )
    pattern_expr = PatternExprOp(
        pattern_id="p1",
        kind="net",
        owner="e1",
        bundles=["b1"],
    )
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        region=[inst, net, bundle, pattern_expr],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_pattern_expr_endpoint_owner_requires_endpoint_id() -> None:
    inst = _make_instance(inst_id="i1", name="U1")
    endpoint = _make_endpoint(endpoint_id="e1", inst_id="i1", port_path="A")
    net = _make_net(net_id="n1", name="N", endpoints=[endpoint])
    bundle = BundleOp(
        bundle_id="b1",
        kind="endpoint",
        base_name="A",
        pattern_type="literal",
        members=["e1"],
    )
    pattern_expr = PatternExprOp(
        pattern_id="p1",
        kind="endpoint",
        owner="n1",
        bundles=["b1"],
    )
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        region=[inst, net, bundle, pattern_expr],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_pattern_expr_param_owner_requires_param_ref() -> None:
    inst = _make_instance(inst_id="i1", name="U1")
    net = _make_net(net_id="n1", name="N", endpoints=[])
    bundle = BundleOp(
        bundle_id="b1",
        kind="param",
        base_name="W",
        pattern_type="literal",
        members=[_make_param_ref(inst_id="i1", name="W")],
    )
    pattern_expr = PatternExprOp(
        pattern_id="p1",
        kind="param",
        owner="i1",
        bundles=["b1"],
    )
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        region=[inst, net, bundle, pattern_expr],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_pattern_expr_param_owner_accepts_param_ref() -> None:
    inst = _make_instance(inst_id="i1", name="U1")
    net = _make_net(net_id="n1", name="N", endpoints=[])
    param_ref = _make_param_ref(inst_id="i1", name="W")
    bundle = BundleOp(
        bundle_id="b1",
        kind="param",
        base_name="W",
        pattern_type="literal",
        members=[param_ref],
    )
    pattern_expr = PatternExprOp(
        pattern_id="p1",
        kind="param",
        owner=param_ref,
        bundles=["b1"],
    )
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        region=[inst, net, bundle, pattern_expr],
    )

    module.verify()


def test_bundle_shared_across_pattern_expr_is_rejected() -> None:
    inst = _make_instance(inst_id="i1", name="U1")
    net = _make_net(net_id="n1", name="N", endpoints=[])
    bundle = BundleOp(
        bundle_id="b1",
        kind="net",
        base_name="N",
        pattern_type="literal",
        members=["n1"],
    )
    first = PatternExprOp(
        pattern_id="p1",
        kind="net",
        owner="n1",
        bundles=["b1"],
    )
    second = PatternExprOp(
        pattern_id="p2",
        kind="net",
        owner="n1",
        bundles=["b1"],
    )
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        region=[inst, net, bundle, first, second],
    )

    with pytest.raises(VerifyException):
        module.verify()
