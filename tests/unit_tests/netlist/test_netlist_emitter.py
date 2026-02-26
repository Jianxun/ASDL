import datetime
from dataclasses import dataclass
from itertools import count
from pathlib import Path

import pytest

from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.emit.backend_config import (
    DEFAULT_PATTERN_RENDERING,
    BackendConfig,
    SystemDeviceTemplate,
)
from asdl.emit.netlist import emit_netlist
from asdl.emit.netlist_ir import (
    NetlistBackend,
    NetlistConn,
    NetlistDesign,
    NetlistDevice,
    NetlistInstance,
    NetlistModule,
    NetlistNet,
    PatternExpressionEntry,
    PatternOrigin,
)

BACKEND_NAME = "sim.ngspice"
DEFAULT_FILE_ID = "design.asdl"


@dataclass(frozen=True)
class StringAttr:
    data: str


def _string_value(value: StringAttr | str) -> str:
    if isinstance(value, StringAttr):
        return value.data
    return str(value)


def ConnAttr(port: StringAttr | str, net: StringAttr | str) -> NetlistConn:
    return NetlistConn(port=_string_value(port), net=_string_value(net))


def BackendOp(
    *,
    name: str,
    template: str,
    params: dict[str, str] | None = None,
    variables: dict[str, str] | None = None,
    props: dict[str, str] | None = None,
) -> NetlistBackend:
    return NetlistBackend(
        name=name,
        template=template,
        params=params,
        variables=variables,
        props=props,
    )


def DeviceOp(
    *,
    name: str,
    ports: list[str],
    params: dict[str, str] | None = None,
    variables: dict[str, str] | None = None,
    region: list[NetlistBackend] | None = None,
    file_id: str = DEFAULT_FILE_ID,
) -> NetlistDevice:
    return NetlistDevice(
        name=name,
        file_id=file_id,
        ports=ports,
        params=params,
        variables=variables,
        backends=list(region or []),
    )


def _coerce_pattern_origin(
    origin: PatternOrigin | tuple[str, int, str, list[object]] | None,
) -> PatternOrigin | None:
    if origin is None:
        return None
    if isinstance(origin, PatternOrigin):
        return origin
    expr_id, segment_index, base_name, parts = origin
    return PatternOrigin(
        expression_id=expr_id,
        segment_index=segment_index,
        base_name=base_name,
        pattern_parts=list(parts),
    )


def InstanceOp(
    *,
    name: str,
    ref: str,
    conns: list[NetlistConn],
    params: dict[str, str] | None = None,
    ref_file_id: str | None = None,
    pattern_origin: PatternOrigin | tuple[str, int, str, list[object]] | None = None,
    src: object | None = None,
) -> NetlistInstance:
    _ = src
    return NetlistInstance(
        name=name,
        ref=ref,
        ref_file_id=ref_file_id or DEFAULT_FILE_ID,
        params=params,
        conns=list(conns),
        pattern_origin=_coerce_pattern_origin(pattern_origin),
    )


def NetOp(
    *, name: str, pattern_origin: PatternOrigin | tuple[str, int, str, list[object]] | None = None
) -> NetlistNet:
    return NetlistNet(
        name=name,
        pattern_origin=_coerce_pattern_origin(pattern_origin),
    )


def ModuleOp(
    *,
    name: str,
    port_order: list[str],
    region: list[object],
    pattern_expression_table: dict[str, PatternExpressionEntry] | None = None,
    file_id: str = DEFAULT_FILE_ID,
) -> NetlistModule:
    nets = [item for item in region if isinstance(item, NetlistNet)]
    instances = [item for item in region if isinstance(item, NetlistInstance)]
    return NetlistModule(
        name=name,
        file_id=file_id,
        ports=port_order,
        nets=nets,
        instances=instances,
        pattern_expression_table=pattern_expression_table,
    )


def DesignOp(
    *,
    region: list[object],
    top: str | None = None,
    entry_file_id: str | None = DEFAULT_FILE_ID,
) -> NetlistDesign:
    modules = [item for item in region if isinstance(item, NetlistModule)]
    devices = [item for item in region if isinstance(item, NetlistDevice)]
    return NetlistDesign(
        modules=modules,
        devices=devices,
        top=top,
        entry_file_id=entry_file_id,
    )


_expr_counter = count(1)


def register_pattern_expression(
    table: dict[str, PatternExpressionEntry],
    *,
    expression: str,
    kind: str,
) -> str:
    expr_id = f"expr{next(_expr_counter)}"
    table[expr_id] = PatternExpressionEntry(expression=expression, kind=kind)
    return expr_id


def encode_pattern_expression_table(
    table: dict[str, PatternExpressionEntry],
) -> dict[str, PatternExpressionEntry] | None:
    return dict(table) if table else None


def _emit_from_graphir(
    design: NetlistDesign,
    **kwargs: object,
) -> tuple[str | None, list[Diagnostic]]:
    return emit_netlist(design, **kwargs)


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


def _dict_attr(values: dict[str, str]) -> dict[str, str]:
    return {key: str(value) for key, value in values.items()}


def _loc(line: int, col: int) -> None:
    _ = (line, col)
    return None


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
    assert [diag.severity for diag in diagnostics] == [Severity.WARNING]
    assert [diag.code for diag in diagnostics] == [format_code("EMIT", 2)]
    assert diagnostics[0].primary_span is None


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


def test_emit_netlist_uses_ordinal_suffix_for_duplicate_module_names() -> None:
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
    entry_name = "amp"
    imported_name = "amp__2"

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

    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.WARNING
    assert diagnostics[0].code == format_code("EMIT", 14)
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


def test_emit_netlist_realizes_view_symbols_and_ordinally_disambiguates_collisions() -> None:
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
    default_file_id = "lib_default.asdl"
    behave_file_id = "lib_behave.asdl"

    default_module = ModuleOp(
        name="amp",
        port_order=["A"],
        file_id=entry_file_id,
        region=[NetOp(name="A")],
    )
    explicit_default_module = ModuleOp(
        name="amp@default",
        port_order=["A"],
        file_id=default_file_id,
        region=[NetOp(name="A")],
    )
    behave_module = ModuleOp(
        name="amp@behave",
        port_order=["A"],
        file_id=behave_file_id,
        region=[NetOp(name="A")],
    )
    top = ModuleOp(
        name="top",
        port_order=["A"],
        file_id="top.asdl",
        region=[
            NetOp(name="A"),
            InstanceOp(
                name="U0",
                ref="amp",
                ref_file_id=entry_file_id,
                conns=[ConnAttr(StringAttr("A"), StringAttr("A"))],
            ),
            InstanceOp(
                name="U1",
                ref="amp@default",
                ref_file_id=default_file_id,
                conns=[ConnAttr(StringAttr("A"), StringAttr("A"))],
            ),
            InstanceOp(
                name="U2",
                ref="amp@behave",
                ref_file_id=behave_file_id,
                conns=[ConnAttr(StringAttr("A"), StringAttr("A"))],
            ),
        ],
    )
    design = DesignOp(
        region=[top, default_module, explicit_default_module, behave_module],
        top="top",
        entry_file_id="top.asdl",
    )

    netlist, diagnostics = _emit_from_graphir(
        design,
        backend_name="test.backend",
        backend_config=backend_config,
        top_as_subckt=True,
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.WARNING
    assert diagnostics[0].code == format_code("EMIT", 14)
    assert netlist == "\n".join(
        [
            "HEADER top",
            ".subckt top A",
            "XU0 A amp",
            "XU1 A amp__2",
            "XU2 A amp_behave",
            ".ends top",
            ".subckt amp A",
            ".ends amp",
            ".subckt amp__2 A",
            ".ends amp__2",
            ".subckt amp_behave A",
            ".ends amp_behave",
            "FOOTER top",
        ]
    )


def test_emit_netlist_disambiguates_decorated_base_collision() -> None:
    backend_config = _backend_config(
        {
            "__subckt_header__": ".subckt {name} {ports}",
            "__subckt_footer__": ".ends {name}",
            "__subckt_call__": "X{name} {ports} {ref}",
            "__netlist_header__": "HEADER {top}",
            "__netlist_footer__": "FOOTER {top}",
        }
    )

    literal = ModuleOp(
        name="amp_behave",
        port_order=["A"],
        file_id="literal.asdl",
        region=[NetOp(name="A")],
    )
    decorated = ModuleOp(
        name="amp@behave",
        port_order=["A"],
        file_id="decorated.asdl",
        region=[NetOp(name="A")],
    )
    top = ModuleOp(
        name="top",
        port_order=["A"],
        file_id="top.asdl",
        region=[
            NetOp(name="A"),
            InstanceOp(
                name="U0",
                ref="amp_behave",
                ref_file_id="literal.asdl",
                conns=[ConnAttr(StringAttr("A"), StringAttr("A"))],
            ),
            InstanceOp(
                name="U1",
                ref="amp@behave",
                ref_file_id="decorated.asdl",
                conns=[ConnAttr(StringAttr("A"), StringAttr("A"))],
            ),
        ],
    )
    design = DesignOp(
        region=[top, literal, decorated],
        top="top",
        entry_file_id="top.asdl",
    )

    netlist, diagnostics = _emit_from_graphir(
        design,
        backend_name="test.backend",
        backend_config=backend_config,
        top_as_subckt=True,
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.WARNING
    assert diagnostics[0].code == format_code("EMIT", 14)
    assert netlist == "\n".join(
        [
            "HEADER top",
            ".subckt top A",
            "XU0 A amp_behave",
            "XU1 A amp_behave__2",
            ".ends top",
            ".subckt amp_behave A",
            ".ends amp_behave",
            ".subckt amp_behave__2 A",
            ".ends amp_behave__2",
            "FOOTER top",
        ]
    )


def test_emit_netlist_reachable_naming_ignores_unreachable_colliders() -> None:
    backend_config = _backend_config(
        {
            "__subckt_header__": ".subckt {name} {ports}",
            "__subckt_footer__": ".ends {name}",
            "__subckt_call__": "X{name} {ports} {ref}",
            "__netlist_header__": "HEADER {top}",
            "__netlist_footer__": "FOOTER {top}",
        }
    )

    reachable = ModuleOp(
        name="amp@behave",
        port_order=["A"],
        file_id="reachable.asdl",
        region=[NetOp(name="A")],
    )
    unreachable = ModuleOp(
        name="amp_behave",
        port_order=["A"],
        file_id="unreachable.asdl",
        region=[NetOp(name="A")],
    )
    top = ModuleOp(
        name="top",
        port_order=["A"],
        file_id="top.asdl",
        region=[
            NetOp(name="A"),
            InstanceOp(
                name="U1",
                ref="amp@behave",
                ref_file_id="reachable.asdl",
                conns=[ConnAttr(StringAttr("A"), StringAttr("A"))],
            ),
        ],
    )
    design = DesignOp(
        region=[top, reachable, unreachable],
        top="top",
        entry_file_id="top.asdl",
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
            "HEADER top",
            ".subckt top A",
            "XU1 A amp_behave",
            ".ends top",
            ".subckt amp_behave A",
            ".ends amp_behave",
            "FOOTER top",
        ]
    )
