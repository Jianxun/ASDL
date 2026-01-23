from __future__ import annotations

from asdl.core.atomized_graph import (
    AtomizedDeviceDef,
    AtomizedEndpoint,
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedNet,
    AtomizedProgramGraph,
)
from asdl.core.verify_atomized_graph import (
    verify_atomized_graph,
    verify_atomized_graph_if_clean,
)
from asdl.diagnostics import Diagnostic, Severity


def _module() -> AtomizedModuleGraph:
    return AtomizedModuleGraph(module_id="m1", name="top", file_id="design.asdl")


def _program(module: AtomizedModuleGraph) -> AtomizedProgramGraph:
    return AtomizedProgramGraph(modules={module.module_id: module})


def test_verify_atomized_graph_reports_duplicate_net_names() -> None:
    module = _module()
    module.nets = {
        "n1": AtomizedNet(net_id="n1", name="NET0", endpoint_ids=[]),
        "n2": AtomizedNet(net_id="n2", name="NET0", endpoint_ids=[]),
    }

    diagnostics = verify_atomized_graph(_program(module))

    assert any(diag.code == "IR-030" for diag in diagnostics)


def test_verify_atomized_graph_reports_duplicate_instance_names() -> None:
    module = _module()
    module.instances = {
        "i1": AtomizedInstance(
            inst_id="i1",
            name="U0",
            ref_kind="device",
            ref_id="d1",
            ref_raw="nmos",
        ),
        "i2": AtomizedInstance(
            inst_id="i2",
            name="U0",
            ref_kind="device",
            ref_id="d1",
            ref_raw="nmos",
        ),
    }

    diagnostics = verify_atomized_graph(_program(module))

    assert any(diag.code == "IR-031" for diag in diagnostics)


def test_verify_atomized_graph_reports_missing_endpoint_refs() -> None:
    module = _module()
    module.endpoints = {
        "e1": AtomizedEndpoint(
            endpoint_id="e1",
            net_id="n1",
            inst_id="i1",
            port="P",
        )
    }

    diagnostics = verify_atomized_graph(_program(module))

    assert [diag.code for diag in diagnostics].count("IR-032") == 2


def test_verify_atomized_graph_reports_invalid_endpoint_port() -> None:
    module = _module()
    module.nets = {
        "n1": AtomizedNet(net_id="n1", name="NET0", endpoint_ids=["e1"])
    }
    module.instances = {
        "i1": AtomizedInstance(
            inst_id="i1",
            name="U0",
            ref_kind="device",
            ref_id="d1",
            ref_raw="nmos",
        )
    }
    module.endpoints = {
        "e1": AtomizedEndpoint(
            endpoint_id="e1",
            net_id="n1",
            inst_id="i1",
            port="S",
        )
    }
    program = _program(module)
    program.devices["d1"] = AtomizedDeviceDef(
        device_id="d1",
        name="nmos",
        file_id="design.asdl",
        ports=["D", "G"],
    )

    diagnostics = verify_atomized_graph(program)

    assert any(diag.code == "IR-033" for diag in diagnostics)


def test_verify_atomized_graph_if_clean_skips_on_error() -> None:
    module = _module()
    module.nets = {
        "n1": AtomizedNet(net_id="n1", name="NET0", endpoint_ids=[]),
        "n2": AtomizedNet(net_id="n2", name="NET0", endpoint_ids=[]),
    }
    program = _program(module)
    existing = [Diagnostic(code="IR-001", severity=Severity.ERROR, message="boom")]

    diagnostics = verify_atomized_graph_if_clean(program, existing)

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "IR-001"
