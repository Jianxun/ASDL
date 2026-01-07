import hashlib
import pytest

pytest.importorskip("xdsl")

from xdsl.dialects.builtin import DictionaryAttr, FileLineColLoc, IntAttr, StringAttr

from asdl.diagnostics import Severity, format_code
from asdl.emit.backend_config import BackendConfig, SystemDeviceTemplate
from asdl.emit.netlist import emit_netlist
from asdl.ir.ifir import (
    BackendOp,
    ConnAttr,
    DesignOp,
    DeviceOp,
    InstanceOp,
    ModuleOp,
    NetOp,
)

BACKEND_NAME = "sim.ngspice"


def _dict_attr(values: dict[str, str]) -> DictionaryAttr:
    return DictionaryAttr({key: StringAttr(value) for key, value in values.items()})


def _loc(line: int, col: int) -> FileLineColLoc:
    return FileLineColLoc(StringAttr("design.asdl"), IntAttr(line), IntAttr(col))


def _backend_config(templates: dict[str, str]) -> BackendConfig:
    return BackendConfig(
        name="test.backend",
        extension="",
        comment_prefix="*",
        templates={
            name: SystemDeviceTemplate(template=template)
            for name, template in templates.items()
        },
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

    netlist, diagnostics = emit_netlist(design)

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


def test_emit_netlist_top_as_subckt_option() -> None:
    module = ModuleOp(
        name="top",
        port_order=["IN"],
        region=[NetOp(name="IN")],
    )
    design = DesignOp(region=[module])

    netlist, diagnostics = emit_netlist(design, top_as_subckt=True)

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

    netlist, diagnostics = emit_netlist(design)

    assert diagnostics == []
    assert netlist == "\n".join(["XP1", ".end"])


def test_emit_netlist_requires_top_when_multiple_modules() -> None:
    module_a = ModuleOp(name="a", port_order=[], region=[])
    module_b = ModuleOp(name="b", port_order=[], region=[])
    design = DesignOp(region=[module_a, module_b])

    netlist, diagnostics = emit_netlist(design)

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

    netlist, diagnostics = emit_netlist(design)

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

    netlist, diagnostics = emit_netlist(design)

    assert diagnostics == []
    assert netlist == "\n".join(["save all", ".end"])


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

    netlist, diagnostics = emit_netlist(design)

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

    netlist, diagnostics = emit_netlist(design)

    assert netlist is not None
    assert "ROVERRIDE VOUT" in netlist
    assert netlist.endswith(".end")
    assert diagnostics == []


def test_emit_netlist_expands_patterns() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports} {model}",
        props=_dict_attr({"model": "nfet"}),
    )
    device = DeviceOp(name="nfet", ports=["D", "G", "S"], region=[backend])
    instance = InstanceOp(
        name="M<1|2>",
        ref="nfet",
        conns=[
            ConnAttr(StringAttr("D"), StringAttr("OUT<P|N>")),
            ConnAttr(StringAttr("G"), StringAttr("VSS")),
            ConnAttr(StringAttr("S"), StringAttr("VSS")),
        ],
    )
    module = ModuleOp(
        name="top",
        port_order=["OUT<P|N>", "VSS"],
        region=[
            NetOp(name="OUT<P|N>"),
            NetOp(name="VSS"),
            instance,
        ],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = emit_netlist(design, top_as_subckt=True)

    assert diagnostics == []
    assert netlist is not None
    lines = [
        line
        for line in netlist.splitlines()
        if line and not line.startswith("*")
    ]
    assert lines == [
        ".subckt top OUT_P OUT_N VSS",
        "M_1 OUT_P VSS VSS nfet",
        "M_2 OUT_N VSS VSS nfet",
        ".ends top",
        ".end",
    ]


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

    netlist, diagnostics = emit_netlist(
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

    netlist, diagnostics = emit_netlist(
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
