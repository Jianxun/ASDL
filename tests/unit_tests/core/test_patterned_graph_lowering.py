from __future__ import annotations

from pathlib import Path

from asdl.ast import (
    AsdlDocument,
    DeviceBackendDecl,
    DeviceDecl,
    InstanceDecl,
    InstanceDefaultsDecl,
    ModuleDecl,
    PatternDecl,
)
from asdl.ast.location import Locatable
from asdl.core import GroupSlice
from asdl.imports import resolve_import_graph
from asdl.lowering import build_patterned_graph, build_patterned_graph_from_import_graph


def _loc(line: int, col: int, length: int = 1, file_name: str = "design.asdl") -> Locatable:
    return Locatable(
        file=file_name,
        start_line=line,
        start_col=col,
        end_line=line,
        end_col=col + length,
    )


def _device_by_name(graph: object, name: str) -> object:
    for device in graph.devices.values():
        if device.name == name:
            return device
    raise AssertionError(f"Missing device '{name}'")


def test_build_patterned_graph_with_groups_and_patterns() -> None:
    module = ModuleDecl.model_construct(
        instances={"U<@cols>": "nmos W=<0|1>"},
        nets={
            "$BUS<@cols>": [
                ["U<@cols>.D", "U<@cols>.G"],
                ["U<@cols>.S"],
            ]
        },
        patterns={"cols": PatternDecl(expr="<0|1>", tag="col")},
    )
    module._loc = _loc(1, 1)
    module._instances_loc["U<@cols>"] = _loc(2, 3)
    module._instance_expr_loc["U<@cols>"] = _loc(2, 10)
    module._nets_loc["$BUS<@cols>"] = _loc(3, 3)
    module._net_endpoint_locs["$BUS<@cols>"] = [_loc(4, 5), _loc(5, 5)]

    device = DeviceDecl(
        ports=["D", "G", "S"],
        parameters=None,
        variables=None,
        backends={"sim.ngspice": DeviceBackendDecl(template="M")},
    )
    document = AsdlDocument.model_construct(
        modules={"top": module},
        devices={"nmos": device},
        top="top",
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert diagnostics == []
    device_def = _device_by_name(graph, "nmos")
    assert device_def.ports == ["D", "G", "S"]
    assert device_def.file_id == "design.asdl"
    backend_templates = graph.registries.device_backend_templates
    assert backend_templates is not None
    assert backend_templates[device_def.device_id] == {"sim.ngspice": "M"}
    module_graph = next(iter(graph.modules.values()))
    assert module_graph.port_order == ["BUS<@cols>"]

    net_id = next(iter(module_graph.nets))
    net_bundle = module_graph.nets[net_id]
    assert net_bundle.endpoint_ids == list(module_graph.endpoints.keys())

    hints = graph.registries.schematic_hints
    assert hints is not None
    assert hints.net_groups[net_id] == [
        GroupSlice(start=0, count=2, label=None),
        GroupSlice(start=2, count=1, label=None),
    ]

    exprs = graph.registries.pattern_expressions
    assert exprs is not None
    expr_by_raw = {expr.raw: expr for expr in exprs.values()}
    assert expr_by_raw["BUS<@cols>"].axis_order == ["col"]

    inst_id = next(iter(module_graph.instances))
    inst_bundle = module_graph.instances[inst_id]
    assert inst_bundle.param_expr_ids is not None
    param_expr_id = inst_bundle.param_expr_ids["W"]
    assert exprs[param_expr_id].raw == "<0|1>"

    origins = graph.registries.pattern_origins
    assert origins is not None
    assert origins[net_id] == (net_bundle.name_expr_id, 0, 0)

    param_origins = graph.registries.param_pattern_origins
    assert param_origins is not None
    assert param_origins[(inst_id, "W")] == (param_expr_id, 0)

    spans = graph.registries.source_spans
    assert spans is not None
    assert spans[net_id].file == "design.asdl"


def test_build_patterned_graph_expr_cache_and_kinds() -> None:
    module = ModuleDecl.model_construct(
        instances={
            "A": "nmos W=<0|1>",
            "B": "nmos W=<0|1>",
        },
        nets={"$A": ["A.D", "B.D", "A.D"]},
    )
    device = DeviceDecl(
        ports=["D", "G"],
        parameters=None,
        variables=None,
        backends={"sim.ngspice": DeviceBackendDecl(template="M")},
    )
    document = AsdlDocument.model_construct(
        modules={"top": module},
        devices={"nmos": device},
        top="top",
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert diagnostics == []
    exprs = graph.registries.pattern_expressions
    kinds = graph.registries.pattern_expr_kinds
    assert exprs is not None
    assert kinds is not None

    module_graph = next(iter(graph.modules.values()))
    net_id = next(iter(module_graph.nets))
    net_expr_id = module_graph.nets[net_id].name_expr_id
    assert exprs[net_expr_id].raw == "A"
    assert kinds[net_expr_id] == "net"

    inst_a = next(
        inst
        for inst in module_graph.instances.values()
        if exprs[inst.name_expr_id].raw == "A"
    )
    inst_b = next(
        inst
        for inst in module_graph.instances.values()
        if exprs[inst.name_expr_id].raw == "B"
    )
    assert inst_a.name_expr_id != net_expr_id
    assert kinds[inst_a.name_expr_id] == "inst"

    assert inst_a.param_expr_ids is not None
    assert inst_b.param_expr_ids is not None
    param_expr_id_a = inst_a.param_expr_ids["W"]
    param_expr_id_b = inst_b.param_expr_ids["W"]
    assert param_expr_id_a == param_expr_id_b
    assert kinds[param_expr_id_a] == "param"

    endpoint_expr_ids = [
        module_graph.endpoints[endpoint_id].port_expr_id
        for endpoint_id in module_graph.nets[net_id].endpoint_ids
    ]
    a_d_expr_ids = [
        expr_id for expr_id in endpoint_expr_ids if exprs[expr_id].raw == "A.D"
    ]
    assert len(a_d_expr_ids) == 2
    assert len(set(a_d_expr_ids)) == 1
    assert kinds[a_d_expr_ids[0]] == "endpoint"


def test_build_patterned_graph_port_order_appends_default_ports() -> None:
    module = ModuleDecl.model_construct(
        instances={"U1": "nmos"},
        nets={
            "$A": ["U1.D"],
            "$B": ["U1.G"],
        },
        instance_defaults={
            "nmos": InstanceDefaultsDecl.model_construct(
                bindings={
                    "G": "$CTRL",
                    "S": "VSS",
                    "B": "$A",
                    "D": "$VDD",
                }
            )
        },
    )
    device = DeviceDecl(
        ports=None,
        parameters=None,
        variables=None,
        backends={"sim.ngspice": DeviceBackendDecl(template="M")},
    )
    document = AsdlDocument.model_construct(
        modules={"top": module},
        devices={"nmos": device},
        top="top",
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert diagnostics == []
    device_def = _device_by_name(graph, "nmos")
    assert device_def.ports == []
    module_graph = next(iter(graph.modules.values()))
    assert module_graph.port_order == ["A", "B", "CTRL", "VDD"]


def test_build_patterned_graph_preserves_module_variables() -> None:
    module = ModuleDecl.model_construct(
        variables={"corner": "tt", "temp": 27},
        instances={},
        nets={},
    )
    document = AsdlDocument.model_construct(
        modules={"top": module},
        devices={},
        top="top",
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert diagnostics == []
    module_graph = next(iter(graph.modules.values()))
    assert module_graph.variables == {"corner": "tt", "temp": 27}


def test_build_patterned_graph_spliced_default_port_emits_ir003() -> None:
    module = ModuleDecl.model_construct(
        instances={"U1": "nmos"},
        nets={"$A": ["U1.D"]},
        instance_defaults={
            "nmos": InstanceDefaultsDecl.model_construct(
                bindings={
                    "G": "$BUS<0|1>;TAIL",
                }
            )
        },
    )
    device = DeviceDecl(
        ports=None,
        parameters=None,
        variables=None,
        backends={"sim.ngspice": DeviceBackendDecl(template="M")},
    )
    document = AsdlDocument.model_construct(
        modules={"top": module},
        devices={"nmos": device},
        top="top",
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert any(diag.code == "IR-003" for diag in diagnostics)
    assert any("splice" in diag.message.lower() for diag in diagnostics)
    module_graph = next(iter(graph.modules.values()))
    assert module_graph.port_order == ["A"]


def test_build_patterned_graph_invalid_instance_expr_emits_ir001() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"M1": "res bad"},
                nets={"OUT": ["M1.P"]},
            )
        },
        devices={
            "res": DeviceDecl(
                ports=None,
                parameters=None,
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="R")},
            )
        },
    )

    _, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert any(diag.code == "IR-001" for diag in diagnostics)


def test_build_patterned_graph_invalid_endpoint_expr_emits_ir002() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"M1": "res"},
                nets={"OUT": ["M1"]},
            )
        },
        devices={
            "res": DeviceDecl(
                ports=None,
                parameters=None,
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="R")},
            )
        },
    )

    _, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert any(diag.code == "IR-002" for diag in diagnostics)


def test_build_patterned_graph_missing_unqualified_ref_emits_ir011() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"X1": "missing"},
            )
        },
        devices={},
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert any(diag.code == "IR-011" for diag in diagnostics)
    module_graph = next(iter(graph.modules.values()))
    assert module_graph.ports == []


def test_build_patterned_graph_ambiguous_unqualified_ref_emits_ir011() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"X1": "cell"},
            ),
            "cell": ModuleDecl(),
        },
        devices={
            "cell": DeviceDecl(
                ports=None,
                parameters=None,
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="C")},
            )
        },
        top="top",
    )

    _, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert any(diag.code == "IR-011" for diag in diagnostics)


def test_build_patterned_graph_pattern_parse_failure_emits_ir003() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"M1": "res"},
                nets={"$BUS<>": ["M1.P"]},
            )
        },
        devices={
            "res": DeviceDecl(
                ports=None,
                parameters=None,
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="R")},
            )
        },
    )

    _, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert any(diag.code == "IR-003" for diag in diagnostics)


def test_build_patterned_graph_spliced_net_name_emits_ir003() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"M1": "res"},
                nets={"NET<0|1>;EXTRA": ["M1.P"]},
            )
        },
        devices={
            "res": DeviceDecl(
                ports=None,
                parameters=None,
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="R")},
            )
        },
    )

    _, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert any(diag.code == "IR-003" for diag in diagnostics)
    assert any("splice" in diag.message.lower() for diag in diagnostics)


def _instance_by_raw(
    module_graph: object,
    expr_ids_by_raw: dict[str, str],
    raw_name: str,
) -> object:
    expr_id = expr_ids_by_raw[raw_name]
    for inst in module_graph.instances.values():
        if inst.name_expr_id == expr_id:
            return inst
    raise AssertionError(f"Missing instance '{raw_name}'")


def test_build_patterned_graph_resolves_imported_refs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    lib_root = tmp_path / "lib"
    lib_root.mkdir()
    lib_file = lib_root / "cells.asdl"
    lib_file.write_text(
        "\n".join(
            [
                "modules:",
                "  child: {}",
                "devices:",
                "  nmos:",
                "    backends:",
                "      sim.ngspice:",
                "        template: M",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    entry_file = tmp_path / "entry.asdl"
    entry_file.write_text(
        "\n".join(
            [
                "imports:",
                "  lib: cells.asdl",
                "modules:",
                "  top:",
                "    instances:",
                "      X1: lib.child",
                "      M1: lib.nmos",
                "    nets:",
                "      OUT: [X1.P, M1.D]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    import_graph, import_diags = resolve_import_graph(
        entry_file,
        lib_roots=[lib_root],
    )

    assert import_diags == []
    assert import_graph is not None

    graph, diagnostics = build_patterned_graph_from_import_graph(import_graph)

    assert diagnostics == []
    device_def = _device_by_name(graph, "nmos")
    assert device_def.file_id == str(lib_file.absolute())
    assert device_def.ports == []
    backend_templates = graph.registries.device_backend_templates
    assert backend_templates is not None
    assert backend_templates[device_def.device_id] == {"sim.ngspice": "M"}
    exprs = graph.registries.pattern_expressions
    assert exprs is not None
    expr_ids_by_raw = {expr.raw: expr_id for expr_id, expr in exprs.items()}
    modules = {(module.name, module.file_id): module for module in graph.modules.values()}
    entry_module = modules[("top", str(entry_file.absolute()))]
    imported_module = modules[("child", str(lib_file.absolute()))]

    inst_module = _instance_by_raw(entry_module, expr_ids_by_raw, "X1")
    assert inst_module.ref_kind == "module"
    assert inst_module.ref_id == imported_module.module_id

    inst_device = _instance_by_raw(entry_module, expr_ids_by_raw, "M1")
    assert inst_device.ref_kind == "device"
    assert inst_device.ref_raw == "lib.nmos"


def test_build_patterned_graph_missing_qualified_namespace_emits_ir010(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    lib_root = tmp_path / "lib"
    lib_root.mkdir()
    lib_file = lib_root / "cells.asdl"
    lib_file.write_text(
        "\n".join(
            [
                "modules:",
                "  child: {}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    entry_file = tmp_path / "entry.asdl"
    entry_file.write_text(
        "\n".join(
            [
                "imports:",
                "  lib: cells.asdl",
                "modules:",
                "  top:",
                "    instances:",
                "      X1: missing.child",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    import_graph, import_diags = resolve_import_graph(entry_file, lib_roots=[lib_root])

    assert import_diags == []
    assert import_graph is not None

    _, diagnostics = build_patterned_graph_from_import_graph(import_graph)

    assert any(diag.code == "IR-010" for diag in diagnostics)


def test_build_patterned_graph_missing_qualified_symbol_emits_ir010(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    lib_root = tmp_path / "lib"
    lib_root.mkdir()
    lib_file = lib_root / "cells.asdl"
    lib_file.write_text(
        "\n".join(
            [
                "modules:",
                "  child: {}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    entry_file = tmp_path / "entry.asdl"
    entry_file.write_text(
        "\n".join(
            [
                "imports:",
                "  lib: cells.asdl",
                "modules:",
                "  top:",
                "    instances:",
                "      X1: lib.missing",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    import_graph, import_diags = resolve_import_graph(entry_file, lib_roots=[lib_root])

    assert import_diags == []
    assert import_graph is not None

    _, diagnostics = build_patterned_graph_from_import_graph(import_graph)

    assert any(diag.code == "IR-010" for diag in diagnostics)


def test_build_patterned_graph_parses_quoted_inline_instance_param_values() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"XCODE": "code cmd='.TRAN 0 10u'"},
                nets={"$OUT": ["XCODE.P"]},
            )
        },
        devices={
            "code": DeviceDecl(
                ports=["P"],
                parameters={"cmd": ""},
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="X")},
            )
        },
        top="top",
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert diagnostics == []
    module_graph = next(iter(graph.modules.values()))
    inst = next(iter(module_graph.instances.values()))
    assert inst.param_expr_ids is not None
    exprs = graph.registries.pattern_expressions
    assert exprs is not None
    cmd_expr_id = inst.param_expr_ids["cmd"]
    assert exprs[cmd_expr_id].raw == ".TRAN 0 10u"


def test_build_patterned_graph_named_patterns_are_stable_inside_quoted_instance_values() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                patterns={"step": PatternDecl(expr="<A|B>")},
                instances={"XCODE": "code cmd='echo <@step> done'"},
                nets={"$OUT": ["XCODE.P"]},
            )
        },
        devices={
            "code": DeviceDecl(
                ports=["P"],
                parameters={"cmd": ""},
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="X")},
            )
        },
        top="top",
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert diagnostics == []
    module_graph = next(iter(graph.modules.values()))
    inst = next(iter(module_graph.instances.values()))
    assert inst.param_expr_ids is not None
    exprs = graph.registries.pattern_expressions
    assert exprs is not None
    cmd_expr_id = inst.param_expr_ids["cmd"]
    assert exprs[cmd_expr_id].raw == "echo <@step> done"


def test_build_patterned_graph_accepts_empty_quoted_inline_instance_param_tokens() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={
                    "XEMPTY_SINGLE": "code cmd=''",
                    "XEMPTY_DOUBLE": 'code cmd=""',
                },
                nets={
                    "$OUTA": ["XEMPTY_SINGLE.P"],
                    "$OUTB": ["XEMPTY_DOUBLE.P"],
                },
            )
        },
        devices={
            "code": DeviceDecl(
                ports=["P"],
                parameters={"cmd": ""},
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="X")},
            )
        },
        top="top",
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    # Empty values remain invalid pattern expressions (IR-003), but the
    # token parser must not reject `key=''`/`key=""` as malformed tokens (IR-001).
    assert not any(diag.code == "IR-001" for diag in diagnostics)
    assert any(diag.code == "IR-003" for diag in diagnostics)


def test_build_patterned_graph_accepts_structured_instance_declaration() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={
                    "R1": InstanceDecl(
                        ref="res",
                        parameters={"r": "2k", "enabled": True},
                    )
                },
                nets={"$OUT": ["R1.P"]},
            )
        },
        devices={
            "res": DeviceDecl(
                ports=["P"],
                parameters={"r": "1k", "enabled": False},
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="R")},
            )
        },
        top="top",
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert diagnostics == []
    module_graph = next(iter(graph.modules.values()))
    inst = next(iter(module_graph.instances.values()))
    assert inst.ref_raw == "res"
    assert inst.param_expr_ids is not None
    exprs = graph.registries.pattern_expressions
    assert exprs is not None
    assert exprs[inst.param_expr_ids["r"]].raw == "2k"
    assert exprs[inst.param_expr_ids["enabled"]].raw == "true"
