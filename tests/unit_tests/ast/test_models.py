import pytest
from pydantic import ValidationError

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, InstanceDecl, ModuleDecl, parse_string


def test_document_requires_modules_or_devices() -> None:
    with pytest.raises(ValidationError):
        AsdlDocument.model_validate({})


def test_document_requires_top_when_multiple_modules() -> None:
    data = {
        "modules": {
            "a": {"nets": {"$A": ["I1.P"]}},
            "b": {"nets": {"$B": ["I2.P"]}},
        }
    }
    with pytest.raises(ValidationError):
        AsdlDocument.model_validate(data)


def test_document_allows_imports() -> None:
    document = AsdlDocument.model_validate({"imports": {"gf": "lib.asdl"}, "modules": {"top": {}}})
    assert document.imports == {"gf": "lib.asdl"}


def test_document_rejects_non_string_import_paths() -> None:
    with pytest.raises(ValidationError):
        AsdlDocument.model_validate({"imports": {"gf": 123}, "modules": {"top": {}}})


def test_device_backend_requires_template() -> None:
    with pytest.raises(ValidationError):
        DeviceBackendDecl.model_validate({})


def test_device_decl_requires_non_empty_backends() -> None:
    with pytest.raises(ValidationError):
        DeviceDecl.model_validate({"ports": ["D"], "backends": {}})


def test_device_decl_allows_missing_ports() -> None:
    device = DeviceDecl.model_validate(
        {"backends": {"ngspice": {"template": "R{name} {ports} {params}"}}}
    )
    assert device.ports is None


def test_device_backend_allows_extra_fields() -> None:
    backend = DeviceBackendDecl.model_validate({"template": "M{inst}", "model": "nfet"})
    assert backend.model == "nfet"


def test_device_decl_rejects_params_field() -> None:
    with pytest.raises(ValidationError):
        DeviceDecl.model_validate(
            {
                "ports": ["D"],
                "params": {"m": 2},
                "backends": {"ngspice": {"template": "R{inst} {ports}"}},
            }
        )


def test_device_backend_rejects_params_field() -> None:
    with pytest.raises(ValidationError):
        DeviceBackendDecl.model_validate({"template": "M{inst}", "params": {"m": 2}})


def test_module_instances_require_string_values() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"instances": {"M1": 123}})


def test_module_instances_accept_structured_values() -> None:
    module = ModuleDecl.model_validate(
        {
            "instances": {
                "M0": "nfet m=2",
                "X0": {"ref": "code", "parameters": {"cmd": ".TRAN 0 10u"}},
            }
        }
    )

    assert module.instances is not None
    assert module.instances["M0"] == "nfet m=2"
    structured = module.instances["X0"]
    assert isinstance(structured, InstanceDecl)
    assert structured.ref == "code"
    assert structured.parameters == {"cmd": ".TRAN 0 10u"}


def test_module_instances_reject_structured_params_alias() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"instances": {"X0": {"ref": "code", "params": {"cmd": "x"}}}})


def test_module_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"exports": {"A": "B"}})


def test_module_accepts_patterns_and_instance_defaults() -> None:
    module = ModuleDecl.model_validate(
        {
            "patterns": {"k": "<1|2>", "bus": {"expr": "<A|B>", "tag": "axis"}},
            "instance_defaults": {"mos": {"bindings": {"B": "$VSS"}}},
        }
    )
    assert module.patterns is not None
    assert module.patterns["k"] == "<1|2>"
    assert module.patterns["bus"].expr == "<A|B>"
    assert module.patterns["bus"].tag == "axis"
    assert module.pattern_axis_id("k") == "k"
    assert module.pattern_axis_id("bus") == "axis"
    assert module.instance_defaults["mos"].bindings == {"B": "$VSS"}


def test_module_rejects_invalid_pattern_group() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"patterns": {"k": "MN<1|2>"}})


def test_module_rejects_invalid_pattern_object_expr() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"patterns": {"k": {"expr": "MN<1|2>"}}})


def test_module_rejects_pattern_object_extra_keys() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate(
            {"patterns": {"k": {"expr": "<1|2>", "tag": "axis", "extra": "nope"}}}
        )


def test_module_rejects_pattern_object_missing_expr() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"patterns": {"k": {"tag": "axis"}}})


def test_module_rejects_pattern_object_non_string_tag() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"patterns": {"k": {"expr": "<1|2>", "tag": 123}}})


def test_module_rejects_pattern_object_invalid_tag_name() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"patterns": {"k": {"expr": "<1|2>", "tag": "<1|2>"}}})


def test_module_rejects_instance_defaults_missing_bindings() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"instance_defaults": {"mos": {}}})


def test_parse_variables_blocks() -> None:
    yaml_content = "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    variables:",
            "      ratio: 2",
            "    instances:",
            "      R1: res r=3k",
            "    nets:",
            "      $IN:",
            "        - R1.P",
            "      $OUT:",
            "        - R1.N",
            "devices:",
            "  res:",
            "    ports: [P, N]",
            "    parameters:",
            "      r: 1k",
            "    variables:",
            "      family: base",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports} {params}\"",
            "        parameters:",
            "          m: 2",
            "        variables:",
            "          corner: fast",
        ]
    )

    document, diagnostics = parse_string(yaml_content)

    assert diagnostics == []
    assert document is not None
    assert document.modules is not None
    assert document.devices is not None

    module = document.modules["top"]
    device = document.devices["res"]
    backend = device.backends["sim.ngspice"]
    assert module.variables == {"ratio": 2}
    assert device.parameters == {"r": "1k"}
    assert device.variables == {"family": "base"}
    assert backend.parameters == {"m": 2}
    assert backend.variables == {"corner": "fast"}
