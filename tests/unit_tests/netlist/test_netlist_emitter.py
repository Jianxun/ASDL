import datetime
import hashlib
from pathlib import Path
import pytest

pytest.importorskip("xdsl")

from xdsl.dialects.builtin import DictionaryAttr, FileLineColLoc, IntAttr, StringAttr

from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.emit.backend_config import (
    DEFAULT_PATTERN_RENDERING,
    BackendConfig,
    SystemDeviceTemplate,
)
from asdl.emit.netlist import emit_netlist
from asdl.ir.graphir import DeviceOp as GraphDeviceOp
from asdl.ir.graphir import EndpointOp as GraphEndpointOp
from asdl.ir.graphir import InstanceOp as GraphInstanceOp
from asdl.ir.graphir import ModuleOp as GraphModuleOp
from asdl.ir.graphir import NetOp as GraphNetOp
from asdl.ir.graphir import ProgramOp as GraphProgramOp
from asdl.ir.ifir import (
    BackendOp,
    ConnAttr,
    DesignOp,
    DeviceOp,
    InstanceOp,
    ModuleOp,
    NetOp,
)
from asdl.ir.patterns import encode_pattern_expression_table, register_pattern_expression

BACKEND_NAME = "sim.ngspice"


class _GraphIdAllocator:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def next(self, prefix: str) -> str:
        count = self._counts.get(prefix, 0) + 1
        self._counts[prefix] = count
        return f"{prefix}{count}"


def _select_symbol(
    symbols_by_name: dict[str, list[str]],
    symbol_index: dict[tuple[str, str | None], str],
    name: str,
    file_id: str | None,
) -> str | None:
    if file_id is not None:
        return symbol_index.get((name, file_id))
    candidates = symbols_by_name.get(name, [])
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        return candidates[-1]
    return None


def _graphir_from_ifir(design: DesignOp) -> GraphProgramOp:
    allocator = _GraphIdAllocator()
    module_ids: dict[tuple[str, str | None], str] = {}
    module_names: dict[str, list[str]] = {}
    device_ids: dict[tuple[str, str | None], str] = {}
    device_names: dict[str, list[str]] = {}

    default_file_id = (
        design.entry_file_id.data if design.entry_file_id is not None else "<string>"
    )

    for op in design.body.block.ops:
        if isinstance(op, ModuleOp):
            file_id = op.file_id.data if op.file_id is not None else default_file_id
            module_id = allocator.next("m")
            module_ids[(op.sym_name.data, file_id)] = module_id
            module_names.setdefault(op.sym_name.data, []).append(module_id)
        elif isinstance(op, DeviceOp):
            file_id = op.file_id.data if op.file_id is not None else default_file_id
            device_id = allocator.next("d")
            device_ids[(op.sym_name.data, file_id)] = device_id
            device_names.setdefault(op.sym_name.data, []).append(device_id)

    program_ops = []
    for op in design.body.block.ops:
        if isinstance(op, ModuleOp):
            file_id = op.file_id.data if op.file_id is not None else default_file_id
            module_id = module_ids[(op.sym_name.data, file_id)]
            inst_ops: list[GraphInstanceOp] = []
            inst_id_map: dict[str, str] = {}
            ifir_instances: list[InstanceOp] = []

            for child in op.body.block.ops:
                if not isinstance(child, InstanceOp):
                    continue
                inst_id = allocator.next("i")
                inst_id_map[child.name_attr.data] = inst_id
                ifir_instances.append(child)
                ref_name = child.ref.root_reference.data
                ref_file_id = (
                    child.ref_file_id.data if child.ref_file_id is not None else None
                )
                ref_id = _select_symbol(
                    module_names, module_ids, ref_name, ref_file_id
                )
                ref_kind = "module"
                if ref_id is None:
                    ref_id = _select_symbol(
                        device_names, device_ids, ref_name, ref_file_id
                    )
                    ref_kind = "device"
                if ref_id is None:
                    raise AssertionError(f"Unknown ref '{ref_name}' for GraphIR conversion")
                annotations = None
                if child.src is not None:
                    annotations = DictionaryAttr({"src": child.src})
                inst_ops.append(
                    GraphInstanceOp(
                        inst_id=inst_id,
                        name=child.name_attr.data,
                        module_ref=(ref_kind, ref_id),
                        module_ref_raw=ref_name,
                        props=child.params,
                        annotations=annotations,
                    )
                )

            net_ops: list[GraphNetOp] = []
            for child in op.body.block.ops:
                if not isinstance(child, NetOp):
                    continue
                endpoints: list[GraphEndpointOp] = []
                for inst in ifir_instances:
                    inst_id = inst_id_map[inst.name_attr.data]
                    for conn in inst.conns.data:
                        if conn.net.data != child.name_attr.data:
                            continue
                        endpoints.append(
                            GraphEndpointOp(
                                endpoint_id=allocator.next("e"),
                                inst_id=inst_id,
                                port_path=conn.port.data,
                            )
                        )
                net_ops.append(
                    GraphNetOp(
                        net_id=allocator.next("n"),
                        name=child.name_attr.data,
                        region=endpoints,
                    )
                )

            program_ops.append(
                GraphModuleOp(
                    module_id=module_id,
                    name=op.sym_name.data,
                    file_id=file_id,
                    port_order=[attr.data for attr in op.port_order.data],
                    region=[*net_ops, *inst_ops],
                )
            )
            continue

        if isinstance(op, DeviceOp):
            file_id = op.file_id.data if op.file_id is not None else default_file_id
            device_id = device_ids[(op.sym_name.data, file_id)]
            backends = [backend.clone() for backend in op.body.block.ops]
            program_ops.append(
                GraphDeviceOp(
                    device_id=device_id,
                    name=op.sym_name.data,
                    file_id=file_id,
                    ports=[attr.data for attr in op.ports.data],
                    params=op.params,
                    variables=op.variables,
                    region=backends,
                )
            )

    entry_id = None
    if design.top is not None:
        top_name = design.top.data
        entry_file_id = (
            design.entry_file_id.data if design.entry_file_id is not None else None
        )
        entry_id = _select_symbol(module_names, module_ids, top_name, entry_file_id)
        if entry_id is None:
            raise AssertionError(f"Top module '{top_name}' missing for GraphIR conversion")
    file_order = None
    if design.entry_file_id is not None:
        file_order = [design.entry_file_id.data]

    return GraphProgramOp(region=program_ops, entry=entry_id, file_order=file_order)


def _emit_from_graphir(
    design: DesignOp,
    **kwargs: object,
) -> tuple[str | None, list[Diagnostic]]:
    program = _graphir_from_ifir(design)
    return emit_netlist(program, **kwargs)


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


@pytest.fixture(autouse=True)
def default_backend_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    config_path = _write_backend_config(tmp_path)
    monkeypatch.setenv("ASDL_BACKEND_CONFIG", str(config_path))
    return config_path


def _dict_attr(values: dict[str, str]) -> DictionaryAttr:
    return DictionaryAttr({key: StringAttr(value) for key, value in values.items()})


def _loc(line: int, col: int) -> FileLineColLoc:
    return FileLineColLoc(StringAttr("design.asdl"), IntAttr(line), IntAttr(col))


def _backend_config(
    templates: dict[str, str],
    pattern_rendering: str | None = None,
) -> BackendConfig:
    rendering = (
        pattern_rendering
        if pattern_rendering is not None
        else DEFAULT_PATTERN_RENDERING
    )
    return BackendConfig(
        name="test.backend",
        extension="",
        comment_prefix="*",
        templates={
            name: SystemDeviceTemplate(template=template)
            for name, template in templates.items()
        },
        pattern_rendering=rendering,
    )


def test_emit_netlist_device_params_and_top_default() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports} {model} {params}",
        params=_dict_attr({"l": "120n", "m": "2"}),
        props=_dict_attr({"model": "nfet"}),
    )
    device = DeviceOp(
        name="nfet",
        ports=["D", "G", "S"],
        params=_dict_attr({"w": "1u", "l": "100n"}),
        region=[backend],
    )
    instance = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[
            ConnAttr(StringAttr("G"), StringAttr("VIN")),
            ConnAttr(StringAttr("S"), StringAttr("VSS")),
            ConnAttr(StringAttr("D"), StringAttr("VOUT")),
        ],
        params=_dict_attr({"m": "4", "nf": "2"}),
        src=_loc(12, 3),
    )
    module = ModuleOp(
        name="top",
        port_order=["VIN", "VOUT", "VSS"],
        region=[
            NetOp(name="VIN"),
            NetOp(name="VOUT"),
            NetOp(name="VSS"),
            instance,
        ],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design)

    expected = "\n".join(
        [
            "M1 VOUT VIN VSS nfet w=1u l=120n m=4",
            ".end",
        ]
    )
    assert netlist == expected
    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.WARNING
    assert diagnostics[0].code == format_code("EMIT", 2)
    assert diagnostics[0].primary_span is not None
    assert diagnostics[0].primary_span.start.line == 12
    assert diagnostics[0].primary_span.start.col == 3


def test_emit_netlist_exposes_variable_placeholders() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports} {model} {temp}",
        variables=_dict_attr({"temp": "85"}),
    )
    device = DeviceOp(
        name="nfet",
        ports=["D"],
        variables=_dict_attr({"model": "nfet", "temp": "25"}),
        region=[backend],
    )
    instance = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
    )
    module = ModuleOp(
        name="top",
        port_order=["OUT"],
        region=[NetOp(name="OUT"), instance],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design)

    assert diagnostics == []
    assert netlist == "\n".join(["M1 OUT nfet 85", ".end"])


def test_emit_netlist_reports_instance_variable_override() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports} {model}",
    )
    device = DeviceOp(
        name="nfet",
        ports=["D"],
        variables=_dict_attr({"model": "nfet"}),
        region=[backend],
    )
    instance = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
        params=_dict_attr({"model": "override"}),
        src=_loc(8, 4),
    )
    module = ModuleOp(
        name="top",
        port_order=["OUT"],
        region=[NetOp(name="OUT"), instance],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design)

    assert netlist is None
    assert any(
        diag.code == format_code("EMIT", 12) and diag.severity is Severity.ERROR
        for diag in diagnostics
    )


def test_emit_netlist_reports_variable_param_collision() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports} {params}",
    )
    device = DeviceOp(
        name="nfet",
        ports=["D"],
        params=_dict_attr({"w": "1u"}),
        variables=_dict_attr({"w": "2u"}),
        region=[backend],
    )
    instance = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
    )
    module = ModuleOp(
        name="top",
        port_order=["OUT"],
        region=[NetOp(name="OUT"), instance],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design)

    assert netlist is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == format_code("EMIT", 13)
    assert diagnostics[0].severity is Severity.ERROR


def test_emit_netlist_reports_variable_prop_collision() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports} {model}",
        props=_dict_attr({"model": "nfet"}),
    )
    device = DeviceOp(
        name="nfet",
        ports=["D"],
        variables=_dict_attr({"model": "override"}),
        region=[backend],
    )
    instance = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
    )
    module = ModuleOp(
        name="top",
        port_order=["OUT"],
        region=[NetOp(name="OUT"), instance],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design)

    assert netlist is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == format_code("EMIT", 13)
    assert diagnostics[0].severity is Severity.ERROR


def test_emit_netlist_top_as_subckt_option() -> None:
    module = ModuleOp(
        name="top",
        port_order=["IN"],
        region=[NetOp(name="IN")],
    )
    design = DesignOp(region=[module])

    netlist, diagnostics = _emit_from_graphir(design, top_as_subckt=True)

    assert diagnostics == []
    assert netlist is not None
    lines = [
        line for line in netlist.splitlines() if line and not line.startswith("*")
    ]
    assert lines[0] == ".subckt top IN"
    assert lines[1] == ".ends top"
    assert lines[2] == ".end"


def test_emit_netlist_allows_portless_device() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="X{name} {params}",
    )
    device = DeviceOp(name="probe", ports=[], region=[backend])
    instance = InstanceOp(name="P1", ref="probe", conns=[])
    module = ModuleOp(name="top", port_order=[], region=[instance])
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design)

    assert diagnostics == []
    assert netlist == "\n".join(["XP1", ".end"])


def test_emit_netlist_requires_top_when_multiple_modules() -> None:
    module_a = ModuleOp(name="a", port_order=[], region=[])
    module_b = ModuleOp(name="b", port_order=[], region=[])
    design = DesignOp(region=[module_a, module_b])

    netlist, diagnostics = _emit_from_graphir(design)

    assert netlist is None
    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.ERROR
    assert diagnostics[0].code == format_code("EMIT", 1)


def test_emit_netlist_requires_top_when_entry_has_no_modules() -> None:
    entry_file_id = "entry.asdl"
    imported_file_id = "lib.asdl"
    module = ModuleOp(
        name="top",
        port_order=[],
        file_id=imported_file_id,
        region=[],
    )
    design = DesignOp(region=[module], entry_file_id=entry_file_id)

    netlist, diagnostics = _emit_from_graphir(design)

    assert netlist is None
    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.ERROR
    assert diagnostics[0].code == format_code("EMIT", 1)


def test_emit_netlist_allows_instruction_template() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="save all",
    )
    device = DeviceOp(name="save", ports=[], region=[backend])
    instance = InstanceOp(name="S1", ref="save", conns=[])
    module = ModuleOp(name="top", port_order=[], region=[instance])
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design)

    assert diagnostics == []
    assert netlist == "\n".join(["save all", ".end"])


def test_emit_netlist_expands_env_vars_in_templates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PDK_PATH", "/pdk")
    backend_config = _backend_config(
        {
            "__subckt_header__": ".subckt {name} {ports} ${PDK_PATH}",
            "__subckt_footer__": ".ends {name}",
            "__subckt_call__": "X{name} {ports} {ref}",
            "__netlist_header__": "HEADER $PDK_PATH",
            "__netlist_footer__": "FOOTER",
        }
    )
    backend = BackendOp(
        name="test.backend",
        template="X{name} {ports} ${PDK_PATH}",
    )
    device = DeviceOp(name="nfet", ports=["D"], region=[backend])
    instance = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
    )
    module = ModuleOp(
        name="top",
        port_order=["OUT"],
        region=[NetOp(name="OUT"), instance],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(
        design,
        backend_name="test.backend",
        backend_config=backend_config,
        top_as_subckt=True,
    )

    assert diagnostics == []
    assert netlist == "\n".join(
        [
            "HEADER /pdk",
            ".subckt top OUT /pdk",
            "XM1 OUT /pdk",
            ".ends top",
            "FOOTER",
        ]
    )


def test_emit_netlist_reports_unresolved_env_vars() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="M{name} {ports} $MISSING_VAR",
    )
    device = DeviceOp(name="nfet", ports=["D"], region=[backend])
    instance = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
    )
    module = ModuleOp(
        name="top",
        port_order=["OUT"],
        region=[NetOp(name="OUT"), instance],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design)

    assert netlist is None
    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.ERROR
    assert diagnostics[0].code == format_code("EMIT", 11)


def test_emit_netlist_reports_malformed_template() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports",
    )
    device = DeviceOp(name="nfet", ports=["D"], region=[backend])
    instance = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("VOUT"))],
    )
    module = ModuleOp(
        name="top",
        port_order=["VOUT"],
        region=[NetOp(name="VOUT"), instance],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design)

    assert netlist is None
    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.ERROR
    assert diagnostics[0].code == format_code("EMIT", 8)


def test_emit_netlist_allows_prop_override() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="R{name} {ports} {params}",
        props=_dict_attr({"name": "OVERRIDE"}),
    )
    device = DeviceOp(name="res", ports=["P"], region=[backend])
    instance = InstanceOp(
        name="R1",
        ref="res",
        conns=[ConnAttr(StringAttr("P"), StringAttr("VOUT"))],
    )
    module = ModuleOp(
        name="top",
        port_order=["VOUT"],
        region=[NetOp(name="VOUT"), instance],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design)

    assert netlist is not None
    assert "ROVERRIDE VOUT" in netlist
    assert netlist.endswith(".end")
    assert diagnostics == []


def test_emit_netlist_assumes_atomized_patterns() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports} {model}",
        props=_dict_attr({"model": "nfet"}),
    )
    device = DeviceOp(name="nfet", ports=["D", "G", "S"], region=[backend])
    inst_p = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[
            ConnAttr(StringAttr("D"), StringAttr("OUTP")),
            ConnAttr(StringAttr("G"), StringAttr("VSS")),
            ConnAttr(StringAttr("S"), StringAttr("VSS")),
        ],
    )
    inst_n = InstanceOp(
        name="M2",
        ref="nfet",
        conns=[
            ConnAttr(StringAttr("D"), StringAttr("OUTN")),
            ConnAttr(StringAttr("G"), StringAttr("VSS")),
            ConnAttr(StringAttr("S"), StringAttr("VSS")),
        ],
    )
    module = ModuleOp(
        name="top",
        port_order=["OUTP", "OUTN", "VSS"],
        region=[
            NetOp(name="OUTP"),
            NetOp(name="OUTN"),
            NetOp(name="VSS"),
            inst_p,
            inst_n,
        ],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design, top_as_subckt=True)

    assert diagnostics == []
    assert netlist is not None
    lines = [
        line
        for line in netlist.splitlines()
        if line and not line.startswith("*")
    ]
    assert lines == [
        ".subckt top OUTP OUTN VSS",
        "M1 OUTP VSS VSS nfet",
        "M2 OUTN VSS VSS nfet",
        ".ends top",
        ".end",
    ]


def test_emit_netlist_uses_atomized_instance_params() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports} {model} {params}",
        props=_dict_attr({"model": "nfet"}),
    )
    device = DeviceOp(
        name="nfet",
        ports=["D"],
        params=_dict_attr({"w": "1u", "m": "1"}),
        region=[backend],
    )
    inst_a = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
        params=_dict_attr({"w": "4", "m": "1"}),
    )
    inst_b = InstanceOp(
        name="M2",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
        params=_dict_attr({"w": "4", "m": "2"}),
    )
    module = ModuleOp(
        name="top",
        port_order=["OUT"],
        region=[NetOp(name="OUT"), inst_a, inst_b],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design)

    assert diagnostics == []
    assert netlist is not None
    lines = [
        line
        for line in netlist.splitlines()
        if line and not line.startswith("*")
    ]
    assert lines == [
        "M1 OUT nfet w=4 m=1",
        "M2 OUT nfet w=4 m=2",
        ".end",
    ]


def test_emit_netlist_uses_literal_names_from_atomized_patterns() -> None:
    table = {}
    inst_expr_id = register_pattern_expression(
        table,
        expression="M<1|2>",
        kind="inst",
    )
    net_expr_id = register_pattern_expression(
        table,
        expression="OUT<P|N>",
        kind="net",
    )
    pattern_table_attr = encode_pattern_expression_table(table)
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports} {model}",
        props=_dict_attr({"model": "nfet"}),
    )
    device = DeviceOp(name="nfet", ports=["D", "G", "S"], region=[backend])
    inst_p = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[
            ConnAttr(StringAttr("D"), StringAttr("OUTP")),
            ConnAttr(StringAttr("G"), StringAttr("VSS")),
            ConnAttr(StringAttr("S"), StringAttr("VSS")),
        ],
        pattern_origin=(inst_expr_id, 0, "M", [1]),
    )
    inst_n = InstanceOp(
        name="M2",
        ref="nfet",
        conns=[
            ConnAttr(StringAttr("D"), StringAttr("OUTN")),
            ConnAttr(StringAttr("G"), StringAttr("VSS")),
            ConnAttr(StringAttr("S"), StringAttr("VSS")),
        ],
        pattern_origin=(inst_expr_id, 0, "M", [2]),
    )
    module = ModuleOp(
        name="top",
        port_order=["OUTP", "OUTN", "VSS"],
        pattern_expression_table=pattern_table_attr,
        region=[
            NetOp(name="OUTP", pattern_origin=(net_expr_id, 0, "OUT", ["P"])),
            NetOp(name="OUTN", pattern_origin=(net_expr_id, 0, "OUT", ["N"])),
            NetOp(name="VSS"),
            inst_p,
            inst_n,
        ],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = _emit_from_graphir(design, top_as_subckt=True)

    assert diagnostics == []
    assert netlist is not None
    assert "M<1|2>" not in netlist
    assert "OUT<P|N>" not in netlist
    assert "M1 OUTP VSS VSS nfet" in netlist
    assert "M2 OUTN VSS VSS nfet" in netlist


def test_emit_netlist_renders_numeric_pattern_parts() -> None:
    table = {}
    inst_expr_id = register_pattern_expression(
        table,
        expression="M<1:2>",
        kind="inst",
    )
    net_expr_id = register_pattern_expression(
        table,
        expression="BUS<1:2>",
        kind="net",
    )
    pattern_table_attr = encode_pattern_expression_table(table)
    backend = BackendOp(
        name="test.backend",
        template="{name} {ports} {model}",
        props=_dict_attr({"model": "nfet"}),
    )
    device = DeviceOp(name="nfet", ports=["D"], region=[backend])
    inst_a = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("BUS1"))],
        pattern_origin=(inst_expr_id, 0, "M", [1]),
    )
    inst_b = InstanceOp(
        name="M2",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("BUS2"))],
        pattern_origin=(inst_expr_id, 0, "M", [2]),
    )
    module = ModuleOp(
        name="top",
        port_order=["BUS1", "BUS2"],
        pattern_expression_table=pattern_table_attr,
        region=[
            NetOp(name="BUS1", pattern_origin=(net_expr_id, 0, "BUS", [1])),
            NetOp(name="BUS2", pattern_origin=(net_expr_id, 0, "BUS", [2])),
            inst_a,
            inst_b,
        ],
    )
    design = DesignOp(region=[module, device], top="top")

    backend_config = _backend_config(
        {
            "__subckt_header__": ".subckt {name} {ports}",
            "__subckt_footer__": ".ends {name}",
            "__subckt_call__": "X{name} {ports} {ref}",
            "__netlist_header__": "",
            "__netlist_footer__": ".end",
        },
        pattern_rendering="[{N}]",
    )

    netlist, diagnostics = emit_netlist(
        design,
        backend_name="test.backend",
        backend_config=backend_config,
        top_as_subckt=True,
    )

    assert diagnostics == []
    assert netlist == "\n".join(
        [
            ".subckt top BUS[1] BUS[2]",
            "M[1] BUS[1] nfet",
            "M[2] BUS[2] nfet",
            ".ends top",
            ".end",
        ]
    )


def test_emit_netlist_exposes_file_id_placeholders() -> None:
    backend_config = _backend_config(
        {
            "__subckt_header__": ".subckt {name} {ports} ; {sym_name} {file_id}",
            "__subckt_footer__": ".ends {name}",
            "__subckt_call__": "X{name} {ports} {ref} ; {sym_name} {file_id}",
            "__netlist_header__": "HEADER {top} {top_sym_name} {file_id}",
            "__netlist_footer__": "FOOTER {top} {top_sym_name} {file_id}",
        }
    )
    entry_file_id = "entry.asdl"
    imported_file_id = "lib.asdl"

    child = ModuleOp(
        name="child",
        port_order=["A"],
        file_id=imported_file_id,
        region=[NetOp(name="A")],
    )
    instance = InstanceOp(
        name="U1",
        ref="child",
        ref_file_id=imported_file_id,
        conns=[ConnAttr(StringAttr("A"), StringAttr("A"))],
    )
    top = ModuleOp(
        name="top",
        port_order=["A"],
        file_id=entry_file_id,
        region=[NetOp(name="A"), instance],
    )
    design = DesignOp(
        region=[top, child],
        top="top",
        entry_file_id=entry_file_id,
    )

    netlist, diagnostics = _emit_from_graphir(
        design,
        backend_name="test.backend",
        backend_config=backend_config,
        top_as_subckt=True,
    )

    assert diagnostics == []
    assert netlist == "\n".join(
        [
            "HEADER top top entry.asdl",
            ".subckt top A ; top entry.asdl",
            "XU1 A child ; child lib.asdl",
            ".ends top",
            ".subckt child A ; child lib.asdl",
            ".ends child",
            "FOOTER top top entry.asdl",
        ]
    )


def test_emit_netlist_exposes_emit_timestamp_placeholders() -> None:
    backend_config = _backend_config(
        {
            "__subckt_header__": ".subckt {name} {ports}",
            "__subckt_footer__": ".ends {name}",
            "__subckt_call__": "X{name} {ports} {ref}",
            "__netlist_header__": "HEADER {emit_date} {emit_time} {top}",
            "__netlist_footer__": "FOOTER {emit_date} {emit_time} {top}",
        }
    )
    emit_timestamp = datetime.datetime(2026, 1, 2, 3, 4, 5)
    module = ModuleOp(
        name="top",
        port_order=["IN"],
        region=[NetOp(name="IN")],
    )
    design = DesignOp(region=[module], top="top")

    netlist, diagnostics = _emit_from_graphir(
        design,
        backend_name="test.backend",
        backend_config=backend_config,
        top_as_subckt=True,
        emit_timestamp=emit_timestamp,
    )

    assert diagnostics == []
    assert netlist == "\n".join(
        [
            "HEADER 2026-01-02 03:04:05 top",
            ".subckt top IN",
            ".ends top",
            "FOOTER 2026-01-02 03:04:05 top",
        ]
    )


def test_emit_netlist_hashes_duplicate_module_names() -> None:
    backend_config = _backend_config(
        {
            "__subckt_header__": ".subckt {name} {ports}",
            "__subckt_footer__": ".ends {name}",
            "__subckt_call__": "X{name} {ports} {ref}",
            "__netlist_header__": "HEADER {top}",
            "__netlist_footer__": "FOOTER {top}",
        }
    )
    entry_file_id = "entry.asdl"
    imported_file_id = "lib.asdl"
    entry_hash = hashlib.sha1(entry_file_id.encode("utf-8")).hexdigest()[:8]
    imported_hash = hashlib.sha1(imported_file_id.encode("utf-8")).hexdigest()[:8]
    entry_name = f"amp__{entry_hash}"
    imported_name = f"amp__{imported_hash}"

    imported = ModuleOp(
        name="amp",
        port_order=["A"],
        file_id=imported_file_id,
        region=[NetOp(name="A")],
    )
    instance = InstanceOp(
        name="U1",
        ref="amp",
        ref_file_id=imported_file_id,
        conns=[ConnAttr(StringAttr("A"), StringAttr("A"))],
    )
    top = ModuleOp(
        name="amp",
        port_order=["A"],
        file_id=entry_file_id,
        region=[NetOp(name="A"), instance],
    )
    design = DesignOp(
        region=[top, imported],
        top="amp",
        entry_file_id=entry_file_id,
    )

    netlist, diagnostics = _emit_from_graphir(
        design,
        backend_name="test.backend",
        backend_config=backend_config,
        top_as_subckt=True,
    )

    assert diagnostics == []
    assert netlist == "\n".join(
        [
            f"HEADER {entry_name}",
            f".subckt {entry_name} A",
            f"XU1 A {imported_name}",
            f".ends {entry_name}",
            f".subckt {imported_name} A",
            f".ends {imported_name}",
            f"FOOTER {entry_name}",
        ]
    )
