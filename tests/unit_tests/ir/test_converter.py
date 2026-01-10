from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, ModuleDecl, parse_string
from asdl.diagnostics import Severity
from asdl.imports import NameEnv, ProgramDB
from asdl.ir import convert_document
from asdl.ir.nfir import BackendOp, DesignOp, DeviceOp, InstanceOp, ModuleOp, NetOp


def test_convert_document_to_nfir() -> None:
    doc = AsdlDocument(
        top="top",
        modules={
            "top": ModuleDecl(
                instances={"M1": "nfet_3p3 m=2"},
                nets={
                    "$VIN": ["M1.G"],
                    "VSS": ["M1.S"],
                },
            )
        },
        devices={
            "nfet_3p3": DeviceDecl(
                ports=["D", "G", "S"],
                params={"w": "1u"},
                backends={
                    "ngspice": DeviceBackendDecl(
                        template="M{inst} {D} {G} {S} {model}",
                        params={"m": 1},
                        model="nfet",
                    )
                },
            )
        },
    )

    design, diagnostics = convert_document(doc)
    assert diagnostics == []
    assert isinstance(design, DesignOp)
    assert design.top is not None
    assert design.top.data == "top"

    module = next(op for op in design.body.block.ops if isinstance(op, ModuleOp))
    nets = [op for op in module.body.block.ops if isinstance(op, NetOp)]
    instances = [op for op in module.body.block.ops if isinstance(op, InstanceOp)]
    assert [item.data for item in module.port_order.data] == ["VIN"]
    assert {net.name_attr.data for net in nets} == {"VIN", "VSS"}
    assert len(instances) == 1
    instance = instances[0]
    assert instance.ref.data == "nfet_3p3"
    assert instance.params is not None
    assert instance.params.data["m"].data == "2"

    device = next(op for op in design.body.block.ops if isinstance(op, DeviceOp))
    backend = next(op for op in device.body.block.ops if isinstance(op, BackendOp))
    assert device.sym_name.data == "nfet_3p3"
    assert backend.name_attr.data == "ngspice"
    assert backend.template.data == "M{inst} {D} {G} {S} {model}"
    assert backend.params is not None
    assert backend.params.data["m"].data == "1"
    assert backend.props is not None
    assert backend.props.data["model"].data == "nfet"


def test_convert_document_preserves_pattern_tokens() -> None:
    doc = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"MN<1|2>": "nfet"},
                nets={
                    "$OUT<P|N>": ["MN<1|2>.D<0|1>"],
                    "BUS[3:0];BUS<4|5>": ["MN<1|2>.S"],
                },
            )
        },
        devices={
            "nfet": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="M{inst} {ports}")}
            )
        },
    )

    design, diagnostics = convert_document(doc)
    assert diagnostics == []
    assert isinstance(design, DesignOp)

    module = next(op for op in design.body.block.ops if isinstance(op, ModuleOp))
    nets = [op for op in module.body.block.ops if isinstance(op, NetOp)]
    instances = [op for op in module.body.block.ops if isinstance(op, InstanceOp)]

    assert [item.data for item in module.port_order.data] == ["OUT<P|N>"]
    assert {net.name_attr.data for net in nets} == {"OUT<P|N>", "BUS[3:0];BUS<4|5>"}
    assert len(instances) == 1
    assert instances[0].name_attr.data == "MN<1|2>"

    out_net = next(net for net in nets if net.name_attr.data == "OUT<P|N>")
    assert out_net.endpoints.data[0].inst.data == "MN<1|2>"
    assert out_net.endpoints.data[0].pin.data == "D<0|1>"


def test_convert_document_applies_instance_defaults_and_ports() -> None:
    doc = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"M1": "mos", "M2": "mos"},
                nets={"$VIN": ["M1.G"]},
                instance_defaults={
                    "mos": {"bindings": {"D": "$VOUT", "S": "VSS", "B": "$VBULK"}}
                },
            )
        },
        devices={
            "mos": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="X{inst} {ports}")}
            )
        },
    )

    design, diagnostics = convert_document(doc)
    assert diagnostics == []
    assert isinstance(design, DesignOp)

    module = next(op for op in design.body.block.ops if isinstance(op, ModuleOp))
    nets = [op for op in module.body.block.ops if isinstance(op, NetOp)]
    net_map = {
        net.name_attr.data: {(ep.inst.data, ep.pin.data) for ep in net.endpoints.data}
        for net in nets
    }

    assert set(net_map.keys()) == {"VIN", "VOUT", "VSS", "VBULK"}
    assert net_map["VIN"] == {("M1", "G")}
    assert net_map["VOUT"] == {("M1", "D"), ("M2", "D")}
    assert net_map["VSS"] == {("M1", "S"), ("M2", "S")}
    assert net_map["VBULK"] == {("M1", "B"), ("M2", "B")}
    assert [item.data for item in module.port_order.data] == ["VIN", "VOUT", "VBULK"]


def test_convert_document_instance_defaults_override_warnings() -> None:
    doc = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"M1": "mos", "M2": "mos"},
                nets={
                    "VSS": ["M1.D", "M2.S"],
                    "VDD": ["!M1.S", "M2.D"],
                },
                instance_defaults={"mos": {"bindings": {"D": "VDD", "S": "VSS"}}},
            )
        },
        devices={
            "mos": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="X{inst} {ports}")}
            )
        },
    )

    design, diagnostics = convert_document(doc)
    assert isinstance(design, DesignOp)
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "LINT-002"
    assert diagnostics[0].severity is Severity.WARNING

    module = next(op for op in design.body.block.ops if isinstance(op, ModuleOp))
    nets = [op for op in module.body.block.ops if isinstance(op, NetOp)]
    net_map = {
        net.name_attr.data: {(ep.inst.data, ep.pin.data) for ep in net.endpoints.data}
        for net in nets
    }
    assert net_map["VSS"] == {("M1", "D"), ("M2", "S")}
    assert net_map["VDD"] == {("M1", "S"), ("M2", "D")}


def test_convert_document_allows_portless_device() -> None:
    doc = AsdlDocument(
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{name} {ports} {params}")}
            )
        }
    )

    design, diagnostics = convert_document(doc)
    assert diagnostics == []
    assert isinstance(design, DesignOp)

    device = next(op for op in design.body.block.ops if isinstance(op, DeviceOp))
    assert device.sym_name.data == "res"
    assert list(device.ports.data) == []


def test_convert_document_rejects_invalid_instance_params() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  m:",
            "    instances:",
            "      M1: nfet_3p3 badtoken",
        ]
    )
    doc, parse_diagnostics = parse_string(
        yaml_content,
        file_path=Path("design.asdl"),
    )
    assert parse_diagnostics == []
    assert doc is not None

    design, diagnostics = convert_document(doc)
    assert design is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "IR-001"
    assert diagnostics[0].severity is Severity.ERROR
    assert diagnostics[0].primary_span is not None
    assert diagnostics[0].primary_span.file == "design.asdl"
    assert diagnostics[0].primary_span.start.line == 4
    assert diagnostics[0].primary_span.start.col == 7


def test_convert_document_rejects_invalid_endpoints() -> None:
    yaml_content = "\n".join(
        [
            "modules:",
            "  m:",
            "    nets:",
            "      VIN: [M1G]",
        ]
    )
    doc, parse_diagnostics = parse_string(
        yaml_content,
        file_path=Path("design.asdl"),
    )
    assert parse_diagnostics == []
    assert doc is not None

    design, diagnostics = convert_document(doc)
    assert design is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "IR-002"
    assert diagnostics[0].severity is Severity.ERROR
    assert diagnostics[0].primary_span is not None
    assert diagnostics[0].primary_span.file == "design.asdl"
    assert diagnostics[0].primary_span.start.line == 4
    assert diagnostics[0].primary_span.start.col == 7


def test_convert_document_resolves_unqualified_locally(tmp_path: Path) -> None:
    entry_file = tmp_path / "entry.asdl"
    doc = AsdlDocument(
        modules={"top": ModuleDecl(instances={"M1": "res"})},
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")}
            )
        },
    )

    program_db, diagnostics = ProgramDB.build({entry_file: doc})
    assert diagnostics == []

    name_env = NameEnv(file_id=entry_file, bindings={})
    design, diagnostics = convert_document(doc, name_env=name_env, program_db=program_db)

    assert diagnostics == []
    assert isinstance(design, DesignOp)


def test_convert_document_propagates_entry_file_id(tmp_path: Path) -> None:
    entry_file = tmp_path / "entry.asdl"
    doc = AsdlDocument(
        top="top",
        modules={"top": ModuleDecl(instances={"M1": "res"})},
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")}
            )
        },
    )

    program_db, diagnostics = ProgramDB.build({entry_file: doc})
    assert diagnostics == []

    name_env = NameEnv(file_id=entry_file, bindings={})
    design, diagnostics = convert_document(doc, name_env=name_env, program_db=program_db)

    assert diagnostics == []
    assert isinstance(design, DesignOp)
    assert design.entry_file_id is not None
    assert design.entry_file_id.data == str(entry_file)

    module = next(op for op in design.body.block.ops if isinstance(op, ModuleOp))
    assert module.file_id is not None
    assert module.file_id.data == str(entry_file)

    device = next(op for op in design.body.block.ops if isinstance(op, DeviceOp))
    assert device.file_id is not None
    assert device.file_id.data == str(entry_file)

    instance = next(op for op in module.body.block.ops if isinstance(op, InstanceOp))
    assert instance.ref_file_id is not None
    assert instance.ref_file_id.data == str(entry_file)


def test_convert_document_unqualified_missing_symbol_emits_error(
    tmp_path: Path,
) -> None:
    entry_file = tmp_path / "entry.asdl"
    dep_file = tmp_path / "dep.asdl"
    entry_doc = AsdlDocument(
        modules={"top": ModuleDecl(instances={"M1": "dep_dev"})},
    )
    dep_doc = AsdlDocument(
        devices={
            "dep_dev": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="X{inst} {ports}")}
            )
        }
    )

    program_db, diagnostics = ProgramDB.build({entry_file: entry_doc, dep_file: dep_doc})
    assert diagnostics == []

    name_env = NameEnv(file_id=entry_file, bindings={"dep": dep_file})
    design, diagnostics = convert_document(entry_doc, name_env=name_env, program_db=program_db)

    assert design is None
    assert len(diagnostics) == 2
    assert {diag.code for diag in diagnostics} == {"IR-011", "LINT-001"}
    assert any(
        diag.code == "IR-011" and diag.severity is Severity.ERROR for diag in diagnostics
    )
    assert any(
        diag.code == "LINT-001" and diag.severity is Severity.WARNING for diag in diagnostics
    )


def test_convert_document_resolves_qualified_symbol(tmp_path: Path) -> None:
    entry_file = tmp_path / "entry.asdl"
    dep_file = tmp_path / "dep.asdl"
    entry_doc = AsdlDocument(
        modules={"top": ModuleDecl(instances={"M1": "lib.res"})},
    )
    dep_doc = AsdlDocument(
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")}
            )
        }
    )

    program_db, diagnostics = ProgramDB.build({entry_file: entry_doc, dep_file: dep_doc})
    assert diagnostics == []

    name_env = NameEnv(file_id=entry_file, bindings={"lib": dep_file})
    design, diagnostics = convert_document(entry_doc, name_env=name_env, program_db=program_db)

    assert diagnostics == []
    assert isinstance(design, DesignOp)

    module = next(op for op in design.body.block.ops if isinstance(op, ModuleOp))
    instance = next(op for op in module.body.block.ops if isinstance(op, InstanceOp))
    assert instance.ref.data == "res"
    assert instance.ref_file_id is not None
    assert instance.ref_file_id.data == str(dep_file)


def test_convert_document_unresolved_qualified_symbol_emits_error(
    tmp_path: Path,
) -> None:
    entry_file = tmp_path / "entry.asdl"
    dep_file = tmp_path / "dep.asdl"
    entry_doc = AsdlDocument(
        modules={"top": ModuleDecl(instances={"M1": "lib.missing"})},
    )
    dep_doc = AsdlDocument(
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")}
            )
        }
    )

    program_db, diagnostics = ProgramDB.build({entry_file: entry_doc, dep_file: dep_doc})
    assert diagnostics == []

    name_env = NameEnv(file_id=entry_file, bindings={"lib": dep_file})
    design, diagnostics = convert_document(entry_doc, name_env=name_env, program_db=program_db)

    assert design is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "IR-010"
    assert diagnostics[0].severity is Severity.ERROR


def test_convert_document_used_import_namespace_no_warning(tmp_path: Path) -> None:
    entry_file = tmp_path / "entry.asdl"
    dep_file = tmp_path / "dep.asdl"
    entry_doc = AsdlDocument(
        imports={"lib": "dep.asdl"},
        modules={"top": ModuleDecl(instances={"M1": "lib.res"})},
    )
    dep_doc = AsdlDocument(
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")}
            )
        }
    )

    program_db, diagnostics = ProgramDB.build({entry_file: entry_doc, dep_file: dep_doc})
    assert diagnostics == []

    name_env = NameEnv(file_id=entry_file, bindings={"lib": dep_file})
    design, diagnostics = convert_document(entry_doc, name_env=name_env, program_db=program_db)

    assert design is not None
    assert diagnostics == []


def test_convert_document_unused_import_emits_warning(tmp_path: Path) -> None:
    entry_file = tmp_path / "entry.asdl"
    dep_file = tmp_path / "dep.asdl"
    entry_doc = AsdlDocument(
        imports={"lib": "dep.asdl"},
        modules={"top": ModuleDecl(instances={"M1": "res"})},
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")}
            )
        },
    )
    dep_doc = AsdlDocument(
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")}
            )
        }
    )

    program_db, diagnostics = ProgramDB.build({entry_file: entry_doc, dep_file: dep_doc})
    assert diagnostics == []

    name_env = NameEnv(file_id=entry_file, bindings={"lib": dep_file})
    design, diagnostics = convert_document(entry_doc, name_env=name_env, program_db=program_db)

    assert design is not None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "LINT-001"
    assert diagnostics[0].severity is Severity.WARNING
