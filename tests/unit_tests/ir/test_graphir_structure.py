import pytest

pytest.importorskip("xdsl")

from xdsl.utils.exceptions import VerifyException

from asdl.ir.graphir import EndpointOp, InstanceOp, ModuleOp, NetOp


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


def _make_endpoint(*, endpoint_id: str, inst_id: str, port_path: str) -> EndpointOp:
    return EndpointOp(endpoint_id=endpoint_id, inst_id=inst_id, port_path=port_path)


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
